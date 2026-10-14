import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import app as app_module


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)

    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_job():
    with app_module.job_lock:
        app_module.job.update({
            "running": False,
            "method": None,
            "status": "Ready to start",
            "progress": 0,
            "total_pages": 0,
            "products_count": 0,
            "elapsed": None,
            "error": None,
            "results": [],
        })

    yield

    with app_module.job_lock:
        app_module.job.update({
            "running": False,
            "method": None,
            "status": "Ready to start",
            "progress": 0,
            "total_pages": 0,
            "products_count": 0,
            "elapsed": None,
            "error": None,
            "results": [],
        })
        