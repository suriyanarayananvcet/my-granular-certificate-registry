import datetime
import io
from pathlib import Path

import pandas as pd
from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from gc_registry.account.services import get_accounts_by_user_id
from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import GranularCertificateBundleCreate
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.device.models import Device
from gc_registry.device.services import get_devices_by_account_id
from gc_registry.logging_config import logger
from gc_registry.storage.models import (
    AllocatedStorageRecord,
    StorageAction,
    StorageRecord,
)
from gc_registry.storage.schemas import (
    AllocatedStorageRecordSubmissionResponse,
    StorageActionResponse,
    StorageRecordBase,
    StorageRecordQueryResponse,
    StorageRecordSubmissionResponse,
)
from gc_registry.storage.services import (
    create_allocated_storage_records_from_submitted_data,
    create_charge_records_from_metering_data,
    get_allocated_storage_records_by_device_id,
    get_device_ids_in_allocated_storage_records,
    issue_sdgcs_against_allocated_records,
)
from gc_registry.user.models import User
from gc_registry.user.validation import (
    validate_user_access,
    validate_user_role,
    validate_user_role_for_storage_validator,
)

# Router initialisation
router = APIRouter(tags=["Storage"])


@router.get("/storage_readings_template", response_class=FileResponse)
def get_storage_readings_template(current_user: User = Depends(get_current_user)):
    """Return the CSV template for storage readings submission."""
    template_path = (
        Path(__file__).parent.parent
        / "static"
        / "templates"
        / "storage_readings_template.csv"
    )

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")

    return FileResponse(
        path=template_path,
        filename="meter_readings_template.csv",
        media_type="text/csv",
    )


@router.get("/storage_allocation_template", response_class=FileResponse)
def get_storage_allocation_template(current_user: User = Depends(get_current_user)):
    """Return the CSV template for storage allocation submission."""
    template_path = (
        Path(__file__).parent.parent
        / "static"
        / "templates"
        / "storage_allocation_template.csv"
    )

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")

    return FileResponse(
        path=template_path,
        filename="storage_allocation_template.csv",
        media_type="text/csv",
    )


@router.post(
    "/submit_storage_records",
    response_model=StorageRecordSubmissionResponse,
    status_code=201,
)
async def submit_storage_records(
    file: UploadFile = File(...),
    deviceID: int = Form(...),
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> StorageRecordSubmissionResponse:
    """Submit a list of Storage Records to the registry."""

    # Can be performed by both Storage Device owners and Storage Validators
    if current_user.role != UserRoles.STORAGE_VALIDATOR:
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    try:
        # Read the uploaded file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode("utf-8"))

        # Convert to DataFrame
        storage_records_df = pd.read_csv(csv_file)
        storage_records_df["device_id"] = deviceID

        # Check that the device ID is associated with an account that the user has access to
        device = Device.by_id(deviceID, read_session)

        logger.info(f"Device: {device}")

        if not device:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {deviceID} not found."
            )

        validate_user_access(current_user, device.account_id, read_session)

        # Create the storage records
        storage_submission_response = create_charge_records_from_metering_data(
            storage_records_df,
            write_session,
            read_session,
            esdb_client,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StorageRecordSubmissionResponse(**storage_submission_response)


@router.post(
    "/submit_allocation_records",
    response_model=AllocatedStorageRecordSubmissionResponse,
    status_code=201,
)
async def create_storage_allocation(
    file: UploadFile = File(...),
    deviceID: int = Form(...),
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> AllocatedStorageRecordSubmissionResponse:
    """Storage Validator Only: Submit a list of Allocated Storage Records to the registry.

    This endpoint depends on there being existing validated Storage Charge/Discharge Records
    that have been submitted for the specified device.
    """
    validate_user_role_for_storage_validator(current_user)

    try:
        # Read the uploaded file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode("utf-8"))

        # Convert to DataFrame and replace NaN values with None
        allocated_storage_records_df = pd.read_csv(csv_file, keep_default_na=False)
        allocated_storage_records_df["device_id"] = deviceID

        # Check that the device ID is associated with an account that the user has access to
        device = Device.by_id(deviceID, read_session)

        logger.info(f"Device: {device}")

        if not device:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {deviceID} not found."
            )

        validate_user_access(current_user, device.account_id, read_session)

        # Create the allocated storage records
        allocated_storage_records = (
            create_allocated_storage_records_from_submitted_data(
                allocated_storage_records_df,
                write_session,
                read_session,
                esdb_client,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not allocated_storage_records:
        raise HTTPException(
            status_code=400,
            detail="No valid allocated storage records were created from the submitted data.",
        )

    return AllocatedStorageRecordSubmissionResponse(
        total_records=len(allocated_storage_records),
        message="Allocation records created successfully.",
    )


@router.post(
    "/issue_sdgcs",
    response_model=list[GranularCertificateBundle],
    status_code=200,
)
def issue_SDGCs(
    allocated_storage_record_ids: list[int],
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """A GC Bundle that has been issued following the verification of a cancelled GC Bundle and the proper allocation of a pair
    of Storage Charge and Discharge Records. The GC Bundle is issued to the Account of the Storage Device, and is identical to
    a GC Bundle issued to a production Device albeit with additional storage-specific attributes as described in the Standard.

    These bundles can be queried using the same GC Bundle query endpoint as regular GC Bundles, but with the additional option to filter
    by the storage_id and the discharging_start_datetime, which is inherited from the allocated SDR.
    """
    if current_user.role != UserRoles.STORAGE_VALIDATOR:
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    try:
        # Retrieve the allocated storage records
        allocated_storage_records = read_session.exec(
            select(AllocatedStorageRecord).where(
                AllocatedStorageRecord.id.in_(allocated_storage_record_ids)  # type: ignore
            )
        ).all()

        # Assert allocation records for a single device have been submitted
        device_ids = [record.device_id for record in allocated_storage_records]
        if len(device_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="Allocation records must be for a single device.",
            )
        device_id = device_ids[0]
        device = Device.by_id(device_id, read_session)

        # Assert the user has access to the specified device
        validate_user_access(current_user, device.account_id, read_session)

        issued_sdgcs = issue_sdgcs_against_allocated_records(
            allocated_storage_record_ids=allocated_storage_record_ids,
            device=device,
            account_id=device.account_id,
            write_session=write_session,
            read_session=read_session,
            esdb_client=esdb_client,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return issued_sdgcs


@router.post(
    "/create_storage_record",
    response_model=StorageRecord,
    status_code=201,
)
def create_storage_record(
    storage_record_base: StorageRecordBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Create a Storage Charge/Discharge Record with the specified properties."""
    validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)
    validate_user_access(current_user, storage_record_base.device_id, read_session)

    storage_record = StorageRecord.create(
        storage_record_base, write_session, read_session, esdb_client
    )

    return storage_record


@router.get(
    "/query_storage_record",
    response_model=StorageRecordQueryResponse,
    status_code=200,
)
def query_SCR(
    scr_query: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Return all storage records from the specified Account that match the provided search criteria."""
    scr_action = StorageAction.create(
        scr_query, write_session, read_session, esdb_client
    )

    return scr_action


@router.post(
    "/withdraw_scr",
    response_model=StorageActionResponse,
    status_code=200,
)
def SCR_withdraw(
    storage_action_base: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """(Issuing Body only) - Withdraw a fixed number of SCRs from the specified Account matching the provided search criteria."""
    scr_action = StorageAction.create(
        storage_action_base, write_session, read_session, esdb_client
    )

    return scr_action


@router.post(
    "/withdraw_sdr",
    response_model=StorageActionResponse,
    status_code=200,
)
def SDR_withdraw(
    storage_action_base: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """(Issuing Body only) - Withdraw a fixed number of SDRs from the specified Account matching the provided search criteria."""
    sdr_action = StorageAction.create(
        storage_action_base, write_session, read_session, esdb_client
    )

    return sdr_action


@router.post(
    "/issue_sdgc",
    response_model=GranularCertificateBundle,
    status_code=200,
)
def issue_SDGC(
    sdgc_create: GranularCertificateBundleCreate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """A GC Bundle that has been issued following the verification of a cancelled GC Bundle and the proper allocation of a pair
    of Storage Charge and Discharge Records. The GC Bundle is issued to the Account of the Storage Device, and is identical to
    a GC Bundle issued to a production Device albeit with additional storage-specific attributes as described in the Standard.

    These bundles can be queried using the same GC Bundle query endpoint as regular GC Bundles, but with the additional option to filter
    by the storage_id and the discharging_start_datetime, which is inherited from the allocated SDR.
    """

    sdgc = GranularCertificateBundle.create(
        sdgc_create, write_session, read_session, esdb_client
    )

    return sdgc


@router.get(
    "/allocated_storage_records/{device_id}",
    response_model=list[AllocatedStorageRecord],
    status_code=200,
)
def get_allocated_storage_records(
    device_id: int,
    current_user: User = Depends(get_current_user),
    created_after: datetime.date | None = None,
    created_before: datetime.date | None = None,
    read_session: Session = Depends(db.get_read_session),
):
    """Retrieve all allocated storage records."""

    user_accounts = get_accounts_by_user_id(current_user.id, read_session)
    if not user_accounts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have any associated accounts.",
        )

    # check that the device_id is valid
    device_ids = get_device_ids_in_allocated_storage_records(read_session)

    if not device_ids or device_id not in device_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found in allocated storage records.",
        )

    # check that the user has permission to access the device
    if current_user.role not in [
        UserRoles.ADMIN,
        UserRoles.PRODUCTION_USER,
        UserRoles.STORAGE_VALIDATOR,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an Admin, Production or Storage Validator to perform this action.",
        )

    # if the user is an Admin, Production User check that the device_id is associated with the user
    if current_user.role in [UserRoles.ADMIN, UserRoles.PRODUCTION_USER]:
        user_devices = []
        for account in user_accounts:
            account_devices = get_devices_by_account_id(account.id, read_session)
            user_devices.extend(account_devices)

        if device_id not in [device.id for device in user_devices]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission to access device with ID {device_id}.",
            )

    if not created_after:
        created_after = (datetime.datetime.now() - datetime.timedelta(days=7)).date()
    if not created_before:
        created_before = datetime.datetime.now().date()

    # Validate the date range
    if created_after and created_before and created_after >= created_before:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="created_after must be before created_before.",
        )
    # check the difference between created_after and created_before is not too large
    date_difference = (created_before - created_after).days
    if date_difference > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 30 days.",
        )

    # Retrieve allocated storage records for the specified device
    allocated_storage_records = get_allocated_storage_records_by_device_id(
        device_id=device_id,
        read_session=read_session,
        created_after=created_after or datetime.date.min,
        created_before=created_before or datetime.date.max,
    )

    return allocated_storage_records
