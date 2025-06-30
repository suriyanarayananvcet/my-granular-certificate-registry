import datetime

from pydantic import BaseModel
from sqlmodel import Field

from gc_registry import utils


class MeasurementReportBase(utils.ActiveRecord):
    device_id: int
    interval_start_datetime: datetime.datetime
    interval_end_datetime: datetime.datetime
    interval_usage: int = Field(
        description="The quantity of energy consumed, produced, or stored in Wh by the device during the specified interval.",
    )
    gross_net_indicator: str = Field(
        description="Indicates whether the usage is gross or net of any losses in the system.",
    )
    is_deleted: bool = Field(default=False)


class MeasurementReportRead(MeasurementReportBase):
    id: int


class MeasurementReportUpdate(BaseModel):
    device_id: int | None = None
    interval_start_datetime: datetime.datetime | None = None
    interval_end_datetime: datetime.datetime | None = None


class MeasurementSubmissionResponse(BaseModel):
    message: str
    first_reading_datetime: datetime.datetime
    last_reading_datetime: datetime.datetime
    total_device_usage: int
