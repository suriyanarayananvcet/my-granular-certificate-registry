import json
from typing import Any

import pandas as pd
from esdbclient import EventStoreDBClient
from fastapi.testclient import TestClient
from sqlmodel import Session

from gc_registry.account.models import Account, AccountWhitelistLink
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.services import create_issuance_id
from gc_registry.device.models import Device
from gc_registry.user.models import User


def test_transfer_certificate(
    api_client: TestClient,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_admin_user: User,
    fake_db_account: Account,
    fake_db_account_2: Account,
    token: str,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
):
    # Test case 1: Try to transfer a certificate without target_id
    test_data_1: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
    }

    response = api_client.post(
        "/certificate/transfer",
        json=test_data_1,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> target_id": {"message": "Field required", "type": "missing"}
        },
        "error_type": "validation_error",
    }

    # Test case 2: Try to transfer a certificate without source_id
    test_data_1.pop("source_id")
    test_data_1["target_id"] = fake_db_account_2.id

    response = api_client.post(
        "/certificate/transfer",
        json=test_data_1,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> source_id": {"message": "Field required", "type": "missing"}
        },
        "error_type": "validation_error",
    }

    # Test case 3: Transfer a certificate successfully

    # Whitelist the source account for the target account
    fake_db_account = write_session.merge(fake_db_account)
    AccountWhitelistLink.create(
        {
            "target_account_id": fake_db_account.id,
            "source_account_id": fake_db_account_2.id,
        },
        write_session,
        read_session,
        esdb_client,
    )
    fake_db_account_2 = write_session.merge(fake_db_account_2)
    AccountWhitelistLink.create(
        {
            "target_account_id": fake_db_account_2.id,
            "source_account_id": fake_db_account.id,
        },
        write_session,
        read_session,
        esdb_client,
    )

    test_data_2: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account_2.id,
    }

    response = api_client.post(
        "/certificate/transfer",
        json=test_data_2,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202

    # Test case 4: Try to transfer a fraction of a certificate
    test_data_3: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account_2.id,
        "target_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.75,
    }

    response = api_client.post(
        "/certificate/transfer",
        json=test_data_3,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202

    # Test case 5: Try to transfer a certificate with invalid percentage

    test_data_4: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account_2.id,
        "certificate_bundle_percentage": 1.5,
    }

    response = api_client.post(
        "/certificate/transfer",
        json=test_data_4,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> certificate_bundle_percentage": {
                "message": "Input should be less than or equal to 1",
                "type": "less_than_equal",
            }
        },
        "error_type": "validation_error",
    }

    # Test case 6: Try to specify the action type
    test_data_5: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.5,
        "action_type": "cancel",
    }

    response = api_client.post(
        "/certificate/transfer",
        json=test_data_5,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body": {
                "message": "Value error, `action_type` cannot be set explicitly.",
                "type": "value_error",
            }
        },
        "error_type": "validation_error",
    }


def test_cancel_certificate_no_source_id(
    api_client: TestClient,
    token: str,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_admin_user: User,
):
    # Test case 1: Try to cancel a certificate without source_id
    test_data_1: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
    }

    response = api_client.post(
        "/certificate/cancel/",
        json=test_data_1,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> source_id": {"message": "Field required", "type": "missing"}
        },
        "error_type": "validation_error",
    }


def test_cancel_certificate_successfully(
    api_client: TestClient,
    token: str,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_admin_user: User,
    fake_db_account: Account,
):
    # Test case 2: Cancel a certificate successfully
    test_data_2: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
    }

    response = api_client.post(
        "/certificate/cancel/",
        json=test_data_2,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202


def test_cancel_certificate_fraction(
    api_client: TestClient,
    token: str,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_admin_user: User,
    fake_db_account: Account,
):
    # Test case 3: Try to cancel a fraction of a certificate
    test_data_3: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.35,
    }

    response = api_client.post(
        "/certificate/cancel/",
        json=test_data_3,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202

    # Test case 4: Try to cancel a certificate with invalid percentage
    test_data_4: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
        "certificate_bundle_percentage": 0,
    }

    response = api_client.post(
        "/certificate/cancel/",
        json=test_data_4,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> certificate_bundle_percentage": {
                "message": "Input should be greater than 0",
                "type": "greater_than",
            }
        },
        "error_type": "validation_error",
    }


def test_query_certificate_bundles(
    api_client: TestClient,
    token: str,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_granular_certificate_bundle_2: GranularCertificateBundle,
    fake_db_admin_user: User,
    fake_db_account: Account,
):
    assert fake_db_granular_certificate_bundle.id is not None
    assert fake_db_admin_user.id is not None
    assert fake_db_account.id is not None

    # Test case 1: Try to query a certificate with correct parameters
    test_data_1: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_1,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
    assert "total_certificate_volume" in response.json().keys()
    assert (
        response.json()["total_certificate_volume"]
        == fake_db_granular_certificate_bundle.bundle_quantity
        + fake_db_granular_certificate_bundle_2.bundle_quantity
    )

    # Test case 2: Try to query a certificate with missing source_id
    test_data_2: dict[str, Any] = {
        "user_id": fake_db_admin_user.id,
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_2,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> source_id": {"message": "Field required", "type": "missing"}
        },
        "error_type": "validation_error",
    }

    # Test case 3: Query certificates based on issuance_ids
    test_data_3: dict[str, Any] = {
        "issuance_ids": [
            create_issuance_id(fake_db_granular_certificate_bundle),
            create_issuance_id(fake_db_granular_certificate_bundle_2),
        ],
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_3,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
    assert "total_certificate_volume" in response.json().keys()
    assert (
        response.json()["total_certificate_volume"]
        == fake_db_granular_certificate_bundle.bundle_quantity
        + fake_db_granular_certificate_bundle_2.bundle_quantity
    )
    assert (
        "id" in response.json()["granular_certificate_bundles"][0].keys()
    ), "ID not in returned data"

    # Test case 4: Query certificates with invalid issuance_ids

    test_data_4: dict[str, Any] = {
        "issuance_ids": ["123-12-03-01 12:12:12"],
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_4,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Invalid issuance ID: 123-12-03-01 12:12:12.",
        "details": {},
        "error_type": "http_error",
    }

    # Test case 5: Query certificates with invalid certificate_period_start and certificate_period_end
    test_data_5: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
        "certificate_period_start": "2024-01-01",
        "certificate_period_end": "2020-01-01",
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_5,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "details": {},
        "error_type": "http_error",
        "message": "certificate_period_end must be greater than certificate_period_start.",
        "status_code": 422,
    }

    # Test case 6: Query certificates with invalid certificate_period_start and certificate_period_end > 30 days
    test_data_6: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
        "certificate_period_start": "2024-01-01",
        "certificate_period_end": "2024-05-01",
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_6,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Difference between certificate_period_start and certificate_period_end must be 30 days or less.",
        "details": {},
        "error_type": "http_error",
    }

    # Test case 7: Query certificates with issuance_ids and certificate_period_start and certificate_period_end
    test_data_7: dict[str, Any] = {
        "issuance_ids": [create_issuance_id(fake_db_granular_certificate_bundle)],
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
        "certificate_period_start": "2024-01-01",
        "certificate_period_end": "2024-01-02",
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_7,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Cannot provide issuance_ids with certificate_period_start or certificate_period_end.",
        "details": {},
        "error_type": "http_error",
    }

    # Test case 8: Query certificates with invalid certificate_period_start and certificate_period_end
    test_data_8: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
        "certificate_period_start": "a date string",
        "certificate_period_end": "another date string",
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_8,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> certificate_period_start": {
                "message": "Input should be a valid datetime or date, invalid character in year",
                "type": "datetime_from_date_parsing",
            },
            "body -> certificate_period_end": {
                "message": "Input should be a valid datetime or date, invalid character in year",
                "type": "datetime_from_date_parsing",
            },
        },
        "error_type": "validation_error",
    }

    # Test case 9: Try giving period start more than 30 days in the past with no end date
    test_data_9: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
        "certificate_period_start": "2023-01-01",
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_9,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "certificate_period_end must be provided if certificate_period_start is more than 30 days ago.",
        "details": {},
        "error_type": "http_error",
    }

    # Test case 10: Try with period end, but no start date
    test_data_10: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
        "certificate_period_end": "2023-01-01",
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_10,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "certificate_period_start must be provided if certificate_period_end is provided.",
        "details": {},
        "error_type": "http_error",
    }

    # Test case 11: Try to query certificates with invalid energy_source
    test_data_11: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_admin_user.id,
        "energy_source": "windy",
    }

    response = api_client.post(
        "/certificate/query",
        json=test_data_11,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "status_code": 422,
        "message": "Validation error occurred",
        "details": {
            "body -> energy_source": {
                "message": "Input should be 'solar_pv', 'wind', 'hydro', 'biomass', 'nuclear', 'electrolysis', 'geothermal', 'battery_storage', 'chp' or 'other'",
                "type": "enum",
            }
        },
        "error_type": "validation_error",
    }


def test_read_certificate_bundle(
    api_client: TestClient,
    token: str,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_granular_certificate_bundle_2: GranularCertificateBundle,
    fake_db_admin_user: User,
    fake_db_account: Account,
):
    response = api_client.get(
        f"/certificate/{fake_db_granular_certificate_bundle.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert (
        response.json()["issuance_id"]
        == fake_db_granular_certificate_bundle.issuance_id
    )


def test_import_certificate_bundles(
    import_device_json: dict,
    api_client: TestClient,
    token: str,
    fake_db_account: Account,
):
    # Use the template CSV
    gc_df = pd.read_csv("gc_registry/tests/data/test_import.csv")

    # Test case 1: Successful import
    response = api_client.post(
        "/certificate/import",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "account_id": str(fake_db_account.id),
            "device_json": json.dumps(import_device_json),
        },
        files={"file": ("test_import.csv", gc_df.to_csv(index=False))},
    )
    print(response.json())
    assert response.status_code == 201
    assert response.json()["message"] == "Certificate bundles imported successfully."

    # Test case 2: Import with invalid account ID
    response = api_client.post(
        "/certificate/import",
        headers={"Authorization": f"Bearer {token}"},
        data={"account_id": str(50000), "device_json": json.dumps(import_device_json)},
        files={"file": ("test_import.csv", gc_df.to_csv(index=False))},
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Account with ID 50000 not found."

    # Test case 3: Import with invalid start and end range IDs
    gc_df_case_3 = gc_df.copy()
    gc_df_case_3["certificate_bundle_id_range_start"] = 50000
    gc_df_case_3["certificate_bundle_id_range_end"] = 49999

    response = api_client.post(
        "/certificate/import",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "account_id": str(fake_db_account.id),
            "device_json": json.dumps(import_device_json),
        },
        files={"file": ("test_import.csv", gc_df_case_3.to_csv(index=False))},
    )

    assert response.status_code == 400
    assert (
        response.json()["message"]
        == "bundle_quantity does not match criteria for equal"
    )

    # Test case 4: Import with invalid bundle quantity
    gc_df_case_4 = gc_df.copy()
    gc_df_case_4["bundle_quantity"] = 100

    response = api_client.post(
        "/certificate/import",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "account_id": str(fake_db_account.id),
            "device_json": json.dumps(import_device_json),
        },
        files={"file": ("test_import.csv", gc_df_case_4.to_csv(index=False))},
    )

    assert response.status_code == 400
    expected_message = "bundle_quantity does not match criteria for equal"
    actual_message = response.json()["message"]
    assert actual_message == expected_message


def test_cancel_for_storage(
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    api_client: TestClient,
    fake_db_admin_user: User,
    fake_db_account: Account,
    fake_db_storage_device: Device,
    token: str,
) -> None:
    # Test case 2: Cancel a certificate successfully
    test_data_2: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_admin_user.id,
        "source_id": fake_db_account.id,
        "storage_local_device_identifier": fake_db_storage_device.local_device_identifier,
    }

    response = api_client.post(
        "/certificate/cancel_for_storage/",
        json=test_data_2,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 202
