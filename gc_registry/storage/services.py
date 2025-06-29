import datetime

from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.storage.models import AllocatedStorageRecord


def get_device_ids_in_allocated_storage_records(read_session: Session) -> list[int]:
    """Retrieve all device IDs that have allocated storage records."""

    # Query the database for unique device IDs in allocated storage records
    device_ids = read_session.exec(
        select(AllocatedStorageRecord.device_id).distinct()
    ).all()

    return list(device_ids)


def get_allocated_storage_records_by_device_id(
    device_id: int,
    read_session: Session,
    created_after: datetime.date,
    created_before: datetime.date,
) -> list[AllocatedStorageRecord] | None:
    """Retrieve all Allocated Storage Records for the specified device."""

    # Query the database for allocated storage records for the specified device
    query: SelectOfScalar = select(AllocatedStorageRecord).where(
        AllocatedStorageRecord.device_id == device_id,
        AllocatedStorageRecord.created_at >= created_after,
        AllocatedStorageRecord.created_at < created_before,
    )

    allocated_storage_records = read_session.exec(query).all()

    return allocated_storage_records
