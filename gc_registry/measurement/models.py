from sqlmodel import Field

from gc_registry.measurement.schemas import MeasurementReportBase


class MeasurementReport(MeasurementReportBase, table=True):
    id: int | None = Field(primary_key=True)
