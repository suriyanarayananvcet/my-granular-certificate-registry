import pandas as pd


def validate_readings(
    df: pd.DataFrame,
) -> tuple[bool, pd.DataFrame, str]:
    """
    Validate the readings in the measurement DataFrame.
    Args:
        measurement_df (pd.DataFrame): DataFrame containing the measurements.
        read_session (Session): SQLAlchemy session for database access.
        device_id (int): ID of the device associated with the measurements.
    Returns:
        tuple[bool, str]: A tuple indicating whether validation passed and an error message if it failed.
    """
    # Check if required columns are present
    required_columns = [
        "interval_start_datetime",
        "interval_end_datetime",
        "interval_usage",
        "gross_net_indicator",
    ]
    if not all(col in df.columns for col in required_columns):
        return False, df, "Missing required columns in measurement data."

    try:
        df["interval_start_datetime"] = pd.to_datetime(
            df["interval_start_datetime"], utc=True
        )
        df["interval_end_datetime"] = pd.to_datetime(
            df["interval_end_datetime"], utc=True
        )
    except Exception as e:
        return False, df, f"Error parsing datetime columns: {str(e)}"

    df["interval_start_datetime"] = df["interval_start_datetime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    df["interval_end_datetime"] = df["interval_end_datetime"].dt.strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    return True, df, ""
