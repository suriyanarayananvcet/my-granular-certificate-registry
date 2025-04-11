import datetime

import pytz

from gc_registry.certificate.services import (
    issue_certificates_metering_integration_for_all_devices_in_date_range,
)
from gc_registry.device.meter_data.elexon.elexon import ElexonClient


def issue_for_all_generators_and_certificates_from_elexon():
    to_datetime = datetime.datetime.now(tz=pytz.UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    from_datetime = to_datetime - datetime.timedelta(days=1, hours=1)

    metering_client = ElexonClient()

    issue_certificates_metering_integration_for_all_devices_in_date_range(
        from_datetime, to_datetime, metering_client
    )


if __name__ == "__main__":
    issue_for_all_generators_and_certificates_from_elexon()
