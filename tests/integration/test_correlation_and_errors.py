"""
Integration tests for Distributed Correlation Headers and Unified API Error Envelope.
"""
import pytest


@pytest.mark.django_db
def test_correlation_headers_generated_when_omitted(api_client):
    """Test response contains generated X-Request-ID and X-Trace-ID headers."""
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert "X-Request-ID" in response
    assert response["X-Request-ID"].startswith("req_")
    assert "X-Trace-ID" in response
    assert response["X-Trace-ID"].startswith("trc_")


@pytest.mark.django_db
def test_client_supplied_request_id_preserved(api_client):
    """Test valid client-supplied X-Request-ID is preserved and echoed back."""
    custom_req_id = "client-trace-abc-12345"
    response = api_client.get("/api/v1/health/", HTTP_X_REQUEST_ID=custom_req_id)
    assert response.status_code == 200
    assert response["X-Request-ID"] == custom_req_id


@pytest.mark.django_db
def test_error_envelope_structure_matches_specification(api_client):
    """
    Test that error responses conform strictly to docs/api/error-model.md schema:
    {
      "error": {
        "code": "...",
        "message": "...",
        "request_id": "...",
        "timestamp": "...",
        "details": [...]
      }
    }
    """
    response = api_client.get("/api/v1/auth/me/")  # Unauthenticated
    assert response.status_code == 401
    data = response.json()

    assert "error" in data
    err = data["error"]
    assert err["code"] == "UNAUTHENTICATED"
    assert "message" in err
    assert "request_id" in err
    assert "timestamp" in err
    assert isinstance(err["details"], list)


@pytest.mark.django_db
def test_validation_error_details_structured(api_client, auth_headers_admin_a):
    """Test schema validation error populates details array with field and issue."""
    bad_payload = {
        "name": "",  # Empty name fails validation
        "code": "",
    }
    response = api_client.post("/api/v1/campuses/", bad_payload, format="json", **auth_headers_admin_a)
    assert response.status_code == 400
    data = response.json()
    err = data["error"]
    assert err["code"] == "VALIDATION_FAILED"
    assert len(err["details"]) > 0
    field_names = [d["field"] for d in err["details"]]
    assert "name" in field_names or "code" in field_names


@pytest.mark.django_db
def test_zero_leakage_on_nonexistent_resource(api_client, auth_headers_student_a):
    """Test that querying a nonexistent UUID produces clean 404 without SQL details."""
    import uuid
    random_uuid = uuid.uuid4()
    response = api_client.get(f"/api/v1/campuses/{random_uuid}/", **auth_headers_student_a)
    assert response.status_code == 404
    body_text = response.content.decode("utf-8")
    assert "Traceback" not in body_text
    assert "SELECT" not in body_text
    assert "pg_catalog" not in body_text
