import base64
import os
from pathlib import Path
from unittest import mock

import pytest
import sh
import yaml
from fastapi.testclient import TestClient

import src.main
from src.models import Config, K8sNamespaces


def kind_available():           # codecov-skip
    """Return `True` if a local KinD cluster is available.

    The implicit assumption is that the cluster was created with the
    `../../integration-test-cluster/start_cluster.sh` script.

    """
    # `start_cluster.sh` will have put the Kubeconfig file here.
    kubeconfig = Path("/tmp/kubeconfig-kind.yaml")
    if not kubeconfig.exists():
        return False

    # Read the cluster certificate from the kubeconfig file.
    conf = yaml.safe_load(kubeconfig.read_text())
    cacert_b64 = conf["clusters"][0]["cluster"]["certificate-authority-data"]

    # Query the cluster version to ascertain that we have a cluster and the
    # correct credentials to access it.
    kubectl = sh.kubectl.bake("--kubeconfig", "/tmp/kubeconfig-kind.yaml")  # type: ignore
    try:
        kubectl("version")  # type: ignore
    except (ImportError, sh.CommandNotFound, sh.ErrorReturnCode_1):         # type: ignore
        return False

    # Create a token for the `admin-access` service account that
    # `start_cluster.sh` will have deployed.
    token = kubectl(["create", "token", "admin-access", "--duration=1000000h"])

    # Create a credentials directory on our local machine. Its layout will
    # mimic that of the `/var/run/secrets/kubernetes.io/serviceaccount/` folder
    # inside a Pod.
    dst_path = Path(os.environ["K8S_CREDENTIALS_PATH"])
    dst_path.mkdir(parents=True, exist_ok=True)

    (dst_path / "ca.crt").write_bytes(base64.b64decode(cacert_b64))
    (dst_path / "token").write_text(token)

    return True


@pytest.fixture
def testenvs():
    """Create env vars and Config for local integration test cluster."""
    # Read the Kubeconfig file for the local KinD cluster.
    kubeconfig = Path("/tmp/kubeconfig-kind.yaml")
    conf = yaml.safe_load(kubeconfig.read_text())

    # Extract the address of the K8s API server and provide in the same
    # environment variable that K8s would use.
    k8surl = conf["clusters"][0]["cluster"]["server"]
    assert k8surl.startswith("https://")
    k8surl = k8surl.partition("https://")[2]
    new_env = {"KUBERNETES_SERVICE_HOST": k8surl}

    # Create a replica of a a Pod environment.
    with mock.patch.dict("os.environ", values=new_env, clear=False):
        # Populate the FastAPI app handle with a `Config` structure like the
        # `main` function would do.
        src.server.FASTAPI_APP.extra["config"] = Config(
            k8s_session=None,
            k8s_url="https://" + os.environ["KUBERNETES_SERVICE_HOST"],
            k8s_creds_path=Path(os.environ["K8S_CREDENTIALS_PATH"])
        )

        # Run test.
        yield

        # Clear the configuration again.
        src.server.FASTAPI_APP.extra.clear()


@pytest.mark.skipif(not kind_available(), reason="No Integration Test Cluster")
class TestIntegration:
    def test_fixture(self, testenvs):
        """Sanity check: the environment variables must be valid."""
        creds_path = Path(os.environ["K8S_CREDENTIALS_PATH"])
        assert creds_path.exists() and creds_path.is_dir()

    def test_get_namespaces(self, testenvs):
        """Query namespaces from actual K8s cluster.

        The test is successful if it returned without error and we got at least
        the "default" and "kube-system" namespace.

        """
        # Run through FastAPI startup routine and then query the
        # `k8s-namespace` endpoint to retrive the namespaces.
        with TestClient(src.server.FASTAPI_APP) as client:
            response = client.get("/k8s-namespaces")
        assert response.status_code == 200

        data = K8sNamespaces.parse_obj(response.json())
        assert "default" in data.namespaces
        assert "kube-system" in data.namespaces
