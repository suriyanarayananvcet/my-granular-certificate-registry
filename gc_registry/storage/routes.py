import datetime

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from gc_registry.account.services import get_accounts_by_user_id
from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import (
    GranularCertificateBundleCreate,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.device.services import get_devices_by_account_id
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
)
from gc_registry.storage.services import (
    get_allocated_storage_records_by_device_id,
    get_device_ids_in_allocated_storage_records,
)
from gc_registry.user.models import User

# Router initialisation
router = APIRouter(tags=["Storage"])


@router.post(
    "/create_scr",
    response_model=StorageRecordBase,
    status_code=201,
)
def create_SCR(
    scr_base: StorageRecord,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Create a Storage Charge Record with the specified properties."""
    scr = StorageRecord.create(scr_base, write_session, read_session, esdb_client)

    return scr


@router.get(
    "/query_scr",
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
    """Return all SCRs from the specified Account that match the provided search criteria."""
    scr_action = StorageAction.create(
        scr_query, write_session, read_session, esdb_client
    )

    return scr_action


@router.post(
    "/create_sdr",
    response_model=StorageRecord,
    status_code=201,
)
def create_SDR(
    sdr_base: StorageRecordBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Create a Storage Discharge Record with the specified properties."""
    sdr = StorageRecord.create(sdr_base, write_session, read_session, esdb_client)

    return sdr


@router.get(
    "/query_sdr",
    response_model=AllocatedStorageRecordSubmissionResponse,
    status_code=200,
)
def query_SDR(
    sdr_query: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Return all SDRs from the specified Account that match the provided search criteria."""
    sdr_action = StorageAction.create(
        sdr_query, write_session, read_session, esdb_client
    )

    return sdr_action


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
