import os
from pathlib import Path
from unittest import mock

import pytest
from starlette.testclient import TestClient

import src
import src.logstreams
import src.main
import src.metrics
import src.server
from src.models import Config


def pytest_configure(*args, **kwargs):
    """Pytest calls this hook on startup."""
    # Set log level to DEBUG for all unit tests.
    src.logstreams.setup("DEBUG")


@src.server.FASTAPI_APP.get("/exception")
async def get_exception():
    """Raise an exception.

    This endpoint exists to verify exception handling inside the application.
    It does not exist in production.

    """
    raise ValueError("Test exception")


@pytest.fixture
def client():
    """Return a fully configured FastAPI client.

    The client itself is the usual FastAPI TestClient, but fixture will
    populate the FastAPI app with a valid configuration, just like the real app
    would do.

    """
    app = src.server.FASTAPI_APP

    app.extra.clear()
    app.extra["config"] = Config(
        k8s_session=None,
        k8s_url="https://" + os.environ["KUBERNETES_SERVICE_HOST"],
        k8s_creds_path=Path(os.environ["K8S_CREDENTIALS_PATH"])
    )

    yield TestClient(app)
