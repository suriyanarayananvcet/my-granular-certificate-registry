from sqlmodel import Field

from gc_registry.storage.schemas import (
    AllocatedStorageRecordBase,
    StorageActionBase,
    StorageRecordBase,
)


class StorageRecord(StorageRecordBase, table=True):
    id: int | None = Field(
        default=None,
        description="A unique identifier for the device. Integers could be used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
    )
    account_id: int = Field(
        foreign_key="account.id",
        description="Each storage record is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    device_id: int = Field(
        foreign_key="device.id",
        description="The Device ID of the Storage Device that is being charged or discharged.",
    )
    is_deleted: bool = Field(default=False)


class AllocatedStorageRecord(AllocatedStorageRecordBase, table=True):
    id: int | None = Field(
        default=None,
        description="A unique identifier for the device. Integers could be used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
    )
    account_id: int = Field(
        foreign_key="account.id",
        description="Each allocated storage record is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    device_id: int = Field(
        foreign_key="device.id",
        description="The Device ID of the Storage Device that is being charged or discharged.",
    )
    scr_allocation_id: int = Field(
        description="The unique ID of the SCR that has been allocated to this matched record.",
        foreign_key="storagerecord.id",
    )
    sdr_allocation_id: int = Field(
        description="The unique ID of the SDR that has been allocated to this matched record.",
        foreign_key="storagerecord.id",
    )
    gc_allocation_id: int = Field(
        description="The unique ID of the cancelled GC Bundle that has been allocated to this matched record.",
        foreign_key="granularcertificatebundle.id",
    )
    sdgc_allocation_id: int = Field(
        description="The unique ID of the SD-GC Bundle that has been issued against this matched record.",
        foreign_key="granularcertificatebundle.id",
    )
    is_deleted: bool = Field(default=False)


class StorageAction(StorageActionBase, table=True):
    """A record of a User's request to the registry to query SCRs/SDRs within a specified Account."""

    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )
