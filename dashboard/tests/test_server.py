import os
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

import src.k8s
import src.server
from src.models import Config


class TestEndpoints:
    @mock.patch.object(src.k8s, "create_session")
    def test_startup_shutdown_ok(self, m_cs):
        """Verify startup/shutdown handlers of FastAPI."""
        # Create a dummy config where the `aiohttp` session is a mock.
        cfg = Config(
            k8s_session=mock.AsyncMock(),
            k8s_url="https://" + os.environ["KUBERNETES_SERVICE_HOST"],
            k8s_creds_path=Path(os.environ["K8S_CREDENTIALS_PATH"])
        )

        # Mock the response of `create_session` to return our `cfg`.
        m_cs.return_value = (cfg, False)

        # Run through the startup and shutdown process of FastAPI.
        with TestClient(src.server.FASTAPI_APP):
            pass

        # The shutdown part must have closed the aiohttp session.
        cfg.k8s_session.close.assert_called_once()

    def test_exception(self, client):
        """Use test endpoint to trigger an exception in the server.

        NOTE: that test endpoint will be installed by the `conftest.py` script
        and does not actually exist in production.

        """
        response = client.get("/exception")
        assert response.status_code == 418
