from unittest.mock import Mock

import app as app_module


def test_running_job_cannot_be_started_twice(client, monkeypatch):
    worker = Mock()

    monkeypatch.setattr(
        app_module.threading,
        "Thread",
        lambda *args, **kwargs: worker,
    )

    payload = {
        "method": "threading",
        "pages": 2,
        "category": "mobile-phone",
        "brand": "samsung",
    }

    first = client.post("/api/start", json=payload)
    second = client.post("/api/start", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409
    worker.start.assert_called_once()


def test_status_does_not_modify_job(client):
    with app_module.job_lock:
        app_module.job["running"] = True
        app_module.job["progress"] = 2
        app_module.job["total_pages"] = 5

    response = client.get("/api/status")

    assert response.status_code == 200

    data = response.get_json()
    assert data["running"] is True
    assert data["progress"] == 2
    assert data["total_pages"] == 5


def test_scraping_exception_is_recorded(monkeypatch):
    def broken_scraper(*args, **kwargs):
        raise RuntimeError("Simulated scraper failure")

    monkeypatch.setattr(
        app_module,
        "scrape_products",
        broken_scraper,
    )

    app_module.run_scraping(
        method="threading",
        category="mobile-phone",
        brand="samsung",
        pages=2,
    )

    with app_module.job_lock:
        assert app_module.job["running"] is False
        assert app_module.job["status"] == "Scraping failed"
        assert "Simulated scraper failure" in app_module.job["error"]