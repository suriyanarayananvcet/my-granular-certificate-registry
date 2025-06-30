

import pandas as pd
from sqlmodel import Session
from gc_registry.settings import settings
from gc_registry.storage.models import StorageRecord
from gc_registry.storage.services import get_latest_storage_record_by_device_id


def validate_storage_records(measurement_df:pd.DataFrame, read_session:Session, device_id:int) -> tuple[bool, str | None]:
    """
    Validate the storage records DataFrame to ensure it meets the required data structure.

    # 1 Check the DataFrame is not empty
    # 2 Check required columns are present based on the StorageRecord schema
    # 3 Validate the timestamp columns can be parsed
    # 4 Validate that it is a continuous time series and does not contain gaps or duplicates
    # 5 Validate that the time-series follows the previous time-series aalready stored in the database
    # 6 Validate that the values are within expected ranges relattive to the device
    
    Args:
        measurement_df (pd.DataFrame): The DataFrame containing storage records.
    
        read_session (Session): The SQLAlchemy session for reading from the database.
        device_id (int): The ID of the device for which the records are being validated.
    Returns:
        tuple[bool, str | None]: A tuple where the first element is a boolean indicating
                                  whether the validation passed, and the second element is
                                  an error message if validation failed, or None if it passed.
    """



    if measurement_df.empty:
        return False, "Measurement DataFrame is empty."
    
    if not all(col in measurement_df.columns for col in StorageRecord.__fields__):
        return False, "Measurement DataFrame is missing required columns."
    
    # Check if timestamp columns can be parsed into UTC datetime
    try:
        measurement_df['flow_start_datetime'] = pd.to_datetime(measurement_df['flow_start_datetime'], utc=True)
        measurement_df['flow_end_datetime'] = pd.to_datetime(measurement_df['flow_end_datetime'], utc=True)
    except Exception as e:
        return False, f"Error parsing datetime columns: {str(e)}"
    
    # Check for continuous time series
    measurement_df.sort_values(by='flow_start_datetime', inplace=True)
    unique_diff = measurement_df['flow_start_datetime'].diff().dropna().unique()
    if len(unique_diff) != 1 and unique_diff[0] != pd.Timedelta(hours=settings.CERTIFICATE_GRANULARITY_HOURS):
        return False, "Measurement DataFrame does not have a continuous time series with correct intervals."
    
    # Check for duplicates in the time series
    if measurement_df['flow_start_datetime'].duplicated().any():
        return False, "Measurement DataFrame contains duplicate timestamps."
    
    # get the last stored record for the device
    last_record = get_latest_storage_record_by_device_id(
        device_id=device_id,
        read_session=read_session
    )

    # check the delta between the last record and the first record in the measurement_df is equal to the expected granularity
    if last_record is not None:
        last_record_time = last_record.flow_start_datetime
        first_measurement_time = measurement_df['flow_start_datetime'].iloc[0]
        expected_delta = pd.Timedelta(hours=settings.CERTIFICATE_GRANULARITY_HOURS)
        
        if first_measurement_time - last_record_time != expected_delta:
            return False, "Measurement DataFrame does not follow the previous time series."
        
    return True, None