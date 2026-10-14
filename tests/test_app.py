from unittest.mock import Mock

import pytest
import app as app_module


@pytest.mark.parametrize(
    "payload",
    [
        {"pages": 0},
        {"pages": -1},
        {"pages": 11},
        {"pages": "abc"},
        {"pages": None},
        {"method": "unknown"},
        {"category": ""},
        {"brand": ""},
    ],
)
def test_start_rejects_invalid_input(client, payload):
    response = client.post("/api/start", json=payload)

    assert response.status_code == 400
    assert response.is_json
    assert "error" in response.get_json()


def test_start_rejects_non_json_body(client):
    response = client.post(
        "/api/start",
        data="this is not json",
        content_type="text/plain",
    )

    assert response.status_code in (200, 400)


def test_status_returns_json(client):
    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    for key in (
        "running",
        "status",
        "progress",
        "total_pages",
        "products_count",
        "error",
        "results",
    ):
        assert key in data


def test_index_returns_successful_response(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Digikala" in response.data


def test_second_job_is_rejected_while_running(client):
    with app_module.job_lock:
        app_module.job["running"] = True

    response = client.post(
        "/api/start",
        json={
            "method": "threading",
            "pages": 3,
            "category": "mobile-phone",
            "brand": "samsung",
        },
    )

    assert response.status_code == 409
    assert "error" in response.get_json()


def test_start_launches_background_worker(client, monkeypatch):
    worker = Mock()

    monkeypatch.setattr(
        app_module.threading,
        "Thread",
        lambda *args, **kwargs: worker,
    )

    response = client.post(
        "/api/start",
        json={
            "method": "threading",
            "pages": 3,
            "category": "mobile-phone",
            "brand": "samsung",
        },
    )

    assert response.status_code == 200
    worker.start.assert_called_once()


def test_invalid_method_is_rejected(client):
    response = client.post(
        "/api/start",
        json={
            "method": "process",
            "pages": 3,
            "category": "mobile-phone",
            "brand": "samsung",
        },
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "pages",
    [
        "1.5",
        [],
        {},
        True,
    ],
)
def test_pages_must_be_integer_in_allowed_range(client, pages):
    response = client.post(
        "/api/start",
        json={
            "method": "threading",
            "pages": pages,
            "category": "mobile-phone",
            "brand": "samsung",
        },
    )

    assert response.status_code == 400
    assert response.is_json
    assert "error" in response.get_json()
