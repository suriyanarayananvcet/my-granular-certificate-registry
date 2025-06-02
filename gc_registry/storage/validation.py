import pandas as pd

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord


def validate_allocated_records(
    allocation_record: pd.Series, sdr: pd.Series, scr: pd.Series
):
    if sdr["is_charging"] or not scr["is_charging"]:
        raise ValueError(f"Invalid flow types for the specified allocation IDs : \
                            {allocation_record['sdr_allocation_id']} and {allocation_record['scr_allocation_id']}")

    if sdr["flow_start_datetime"] < scr["flow_end_datetime"]:
        raise ValueError(f"SDR flow start datetime is after SCR flow end datetime: \
                            {allocation_record['sdr_allocation_id']} and {allocation_record['scr_allocation_id']}")

    return


def validate_allocated_records_against_gc_bundles(
    allocated_storage_records: list[AllocatedStorageRecord],
    charge_records: list[StorageRecord],
    gc_bundles: list[GranularCertificateBundle],
):
    """Given a list of allocated storage records, verify that the linked GC
    Bundles sufficient quantities and datetimes to cover the allocated storage records.

    Args:
        allocated_storage_records (list[AllocatedStorageRecord]): A list of allocated storage records.
        charge_records (list[StorageRecord]): A list of SCR and SDR records referenced by the allocated storage records.
        gc_bundles (list[GranularCertificateBundle]): A list of GC Bundles.

    Raises:
        ValueError: If the GC Bundles do not have sufficient quantities or datetimes to cover the allocated storage records.
    """

    for allocated_storage_record in allocated_storage_records:
        gc_bundle = next(
            (
                bundle
                for bundle in gc_bundles
                if bundle.id == allocated_storage_record.gc_allocation_id
            ),
            None,
        )

        scr_record = next(
            (
                record
                for record in charge_records
                if record.id == allocated_storage_record.scr_allocation_id
            ),
            None,
        )

        sdr_record = next(
            (
                record
                for record in charge_records
                if record.id == allocated_storage_record.sdr_allocation_id
            ),
            None,
        )

        if not gc_bundle:
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} not found"
            )

        if (
            gc_bundle.quantity
            != allocated_storage_record.sdr_proportion * scr_record.flow_energy
        ):
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} does not have sufficient quantity"
            )

        if gc_bundle.start_datetime < scr_record.flow_start_datetime:
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} does not have sufficient start datetime"
            )

        if gc_bundle.end_datetime > scr_record.flow_end_datetime:
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} does not have sufficient end datetime"
            )

    return
