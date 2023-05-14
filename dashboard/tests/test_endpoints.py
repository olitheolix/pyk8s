from unittest import mock

import src.k8s
from src.models import K8sNamespaces


class TestBasic:
    def test_404(self, client):
        """Must not break for missing URLs."""
        resp = client.get("/does-not-exist")
        assert resp.status_code == 404

    def test_healthz(self, client):
        """Basic health check."""
        response = client.get("/healthz")
        assert response.status_code == 200


class TestK8sNamespaces:
    @mock.patch.object(src.k8s, "get_namespaces")
    def test_get_k8s_namespaces_ok(self, m_getk8sres, client):
        """Pretend K8s returned the namespaces."""
        # Mock the K8s response.
        m_getk8sres.return_value = (K8sNamespaces(namespaces=["foo", "bar"]), False)

        # Call the endpoint and verify it returns the expected data.
        response = client.get("/k8s-namespaces")
        assert response.status_code == 200
        assert m_getk8sres.called_once_with(client.app.extra["config"])
        assert response.json() == K8sNamespaces(namespaces=["foo", "bar"])

    @mock.patch.object(src.k8s, "get_namespaces")
    def test_get_k8s_namespaces_err(self, m_getk8sres, client):
        """Must gracefully handle the case where `get_namespaces` returned an error."""
        # Mock the K8s response.
        m_getk8sres.return_value = (K8sNamespaces(namespaces=[]), True)

        # Call the endpoint and verify it returns the expected data.
        response = client.get("/k8s-namespaces")
        assert response.status_code == 422
        assert m_getk8sres.called_once_with(client.app.extra["config"])
        assert response.json() == K8sNamespaces(namespaces=[])
