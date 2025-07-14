from fastapi.testclient import TestClient


class TestApiKeyRoutes:
    def _create_api_key(self, client: TestClient, token: str) -> dict:
        """Helper that creates an API key and returns the response payload."""
        client.headers["Authorization"] = f"Bearer {token}"
        response = client.post(
            "/auth/api-key",
            json={"name": "route-test-key", "expires_days": 30},
        )
        assert response.status_code == 200
        return response.json()

    def test_api_key_lifecycle(self, api_client: TestClient, token: str):
        # ---------------------------------------------------------------- create
        key_payload = self._create_api_key(api_client, token)
        api_key_value = key_payload["key"]
        api_key_id = key_payload["id"]

        # ---------------------------------------------------------------- list (Bearer)
        api_client.headers["Authorization"] = f"Bearer {token}"
        resp_list = api_client.get("/auth/api-keys")
        assert resp_list.status_code == 200
        assert any(k["id"] == api_key_id for k in resp_list.json())

        # ---------------------------------------------------------------- list (API Key)
        api_client.headers["Authorization"] = f"API Key {api_key_value}"
        resp_list_key = api_client.get("/auth/api-keys")
        assert resp_list_key.status_code == 200
        assert any(k["id"] == api_key_id for k in resp_list_key.json())

        # -------------------------------------------------------------- deactivate
        api_client.headers["Authorization"] = f"Bearer {token}"
        del_resp = api_client.delete(f"/auth/api-key/{api_key_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["message"] == "API key deactivated successfully"

        # Confirm key is now inactive
        resp_after = api_client.get("/auth/api-keys")
        key_info = next(item for item in resp_after.json() if item["id"] == api_key_id)
        assert key_info["is_active"] is False

    def test_contextual_error_messages(self, api_client: TestClient):
        """Ensure distinct messages for JWT vs API-key failures."""
        # Invalid JWT token
        api_client.headers["Authorization"] = "Bearer notatoken"
        jwt_resp = api_client.get("/auth/api-keys")
        assert jwt_resp.status_code == 401
        assert jwt_resp.json()["message"] == "Invalid or expired JWT access-token"

        # Invalid API key
        api_client.headers["Authorization"] = "API Key not-a-real-key"
        key_resp = api_client.get("/auth/api-keys")
        assert key_resp.status_code == 401
        assert key_resp.json()["message"] == "Invalid or expired API key"
