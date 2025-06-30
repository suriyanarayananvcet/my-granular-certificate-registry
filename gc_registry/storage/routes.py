from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends
import datetime
import io

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import pandas as pd
from sqlmodel import Session
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
from gc_registry.device.services import get_device_by_id, get_devices_by_account_id
from gc_registry.measurement.models import MeasurementReport, MeasurementSubmissionResponse
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
from gc_registry.storage.validation import validate_storage_records
from gc_registry.user.models import User
from gc_registry.user.validation import validate_user_access, validate_user_role
from gc_registry.user.validation import (
    validate_user_access,
    validate_user_role,
    validate_user_role_for_storage_validator,
)

# Router initialisation
router = APIRouter(tags=["Storage"])


@router.post("/storage_charge_records", response_model=MeasurementSubmissionResponse)
async def submit_storage_charge_records(
    file: UploadFile = File(...),
    device_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Submit meter readings as a CSV file for a single device,
    creating a MeasurementReport for each production interval against which GC
    Bundles can be issued. Returns a summary of the readings submitted.

    Until an issuance metadata workflow is implemented, the submission will use a
    default set of issuance metadata. In the front end, this will be implemented as
    a dialogue box that presents the user with the default metadata values, and allow
    them to edit them if desired at the point of issuance.

    Args:
        file (UploadFile): The CSV file containing meter readings
        device_id (int): The ID of the device the readings are for

    Returns:
        models.MeasurementSubmissionResponse: A summary of the readings submitted.
    """
    validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    # Read the uploaded file
    contents = await file.read()
    csv_file = io.StringIO(contents.decode("utf-8"))

    # Convert to DataFrame
    df = pd.read_csv(csv_file)
    df["device_id"] = device_id

    # Check that the device ID is associated with an account that the user has access to
    device = get_device_by_id(read_session,device_id)

    if not device:
        raise HTTPException(
            status_code=404, detail=f"Device with ID {device_id} not found."
        )
    
    if not device.is_storage:
        raise HTTPException(
            status_code=400, detail=f"Device with ID {device_id} is not a storage device."
        )

    validate_user_access(current_user, device.account_id, read_session)

    passed, message = validate_storage_records(df, read_session, device_id)
    if not passed:
        raise HTTPException(
            status_code=400, detail=f"Invalid measurement data: {message}"
        )
    
    df['is_charging'] = df.flow_energy > 0

    storage_records = StorageRecord.create(
        df.to_dict(orient="records"),
        write_session,
        read_session,
        esdb_client,
    )

    if not storage_records:
        raise HTTPException(
            status_code=500, detail="Could not create measurement reports."
        )
    
    # Create a MeasurementReport for the submitted storage records
    measurement_response = MeasurementSubmissionResponse(
        message="Storage Charge Records submitted successfully.",
        first_reading_datetime=df.flow_start_datetime.min(),
        last_reading_datetime=df.flow_start_datetime.max(),
        total_device_usage= int(df.interval_usage.sum()),
    )

    return measurement_response

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
