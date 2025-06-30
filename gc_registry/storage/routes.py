from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends
import datetime
import io

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import pandas as pd
from sqlmodel import Session

from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import (
    GranularCertificateBundleCreate,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.device.services import get_device_by_id, get_devices_by_account_id
from gc_registry.measurement.models import MeasurementReport, MeasurementSubmissionResponse
from gc_registry.storage.models import (
    StorageAction,
    StorageRecord,
)
from gc_registry.storage.schemas import (
    AllocatedStorageRecordSubmissionResponse,
    StorageActionResponse,
    StorageRecordBase,
    StorageRecordQueryResponse,
)
from gc_registry.storage.validation import validate_storage_records
from gc_registry.user.models import User
from gc_registry.user.validation import validate_user_access, validate_user_role

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
