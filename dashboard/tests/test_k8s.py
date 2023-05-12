import os
from pathlib import Path

import aiohttp
import pytest
from aioresponses import aioresponses

import src.k8s
from src.models import Config

# Convenience.
K8S_URL = os.environ["KUBERNETES_SERVICE_HOST"]


class TestConfiguration:
    def test_create_session_ok(self):
        """Test function must construct a valid session object."""
        # Valid input configuration.
        cfg = Config(
            k8s_session=None,
            k8s_url="https://" + os.environ["KUBERNETES_SERVICE_HOST"],
            k8s_creds_path=Path("tests/support"),
        )

        # Sanity check the input `cfg`, most notably that the files really do exist.
        assert cfg.k8s_creds_path.exists()
        assert (cfg.k8s_creds_path / "ca.crt").exists()
        assert (cfg.k8s_creds_path / "token").exists()

        # Test function must create a session object.
        assert cfg.k8s_session is None
        cfg, err = src.k8s.create_session(cfg)
        assert not err and cfg.k8s_session is not None

    def test_create_session_err(self):
        """Gracefully handle invalid or incomplete configuration."""
        # Input configuration with invalid credentials path.
        cfg = Config(
            k8s_session=None,
            k8s_url="https://" + os.environ["KUBERNETES_SERVICE_HOST"],
            k8s_creds_path=Path("/does/not/exist"),
        )

        # Gracefully handle non-existing credentials path.
        cfg, err = src.k8s.create_session(cfg)
        assert err and cfg.k8s_session is None


@pytest.mark.asyncio
class TestK8s:
    async def test_get_k8s_namespaces_simple_ok(self):
        """Verify test function with a mocked K8s response.

        This test is very basic. The mocked API returns an empty list of
        namespaces only.

        """
        with aioresponses() as m:
            # Mock the K8s request to return our dummy manifests.
            m.get(K8S_URL + "/api/v1/namespaces", payload={"items": []})

            # Function must return without error and an empty list of namespaces.
            async with aiohttp.ClientSession() as sess:
                resp, err = await src.k8s.get_namespaces(sess, K8S_URL)
            m.assert_called_once_with(K8S_URL + "/api/v1/namespaces")
            assert not err and resp.namespaces == []

    async def test_get_k8s_namespaces_items_ok(self):
        """Verify test function with a mocked K8s response.

        Unlike the previous test, here the mocked API returns two namespace
        manifests that the test function must unpack.

        """
        # Mocked K8s response: two namespace manifests.
        k8s_resp = {"items": [
            {"metadata": {"name": "foo"}},
            {"metadata": {"name": "bar"}},
        ]}

        with aioresponses() as m:
            # Mock the K8s request to return our dummy manifests.
            m.get(K8S_URL + "/api/v1/namespaces", payload=k8s_resp)

            # Function must return the names of the two namespaces.
            async with aiohttp.ClientSession() as sess:
                resp, err = await src.k8s.get_namespaces(sess, K8S_URL)
            assert not err and resp.namespaces == ["foo", "bar"]

    async def test_get_k8s_namespaces_err(self):
        """Simulate a permission denied error with the K8s API."""
        with aioresponses() as m:
            # Mock the K8s request to return our dummy manifests.
            m.get(K8S_URL + "/api/v1/namespaces", payload={"items": []}, status=403)

            # Test function must gracefully handle an error from the K8s API.
            async with aiohttp.ClientSession() as sess:
                resp, err = await src.k8s.get_namespaces(sess, K8S_URL)
            assert err and resp.namespaces == []
