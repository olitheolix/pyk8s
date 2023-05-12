import logging
import os
import ssl
from pathlib import Path
from typing import Tuple

import aiohttp

from src.models import Config, K8sNamespaces

# Convenience.
logit = logging.getLogger("app")


def create_session(cfg: Config) -> Tuple[Config, bool]:
    """Add a K8s session to the `cfg` model."""
    # Construct the path to the certificate and token.
    fname_cert = cfg.k8s_creds_path / "ca.crt"
    fname_token = cfg.k8s_creds_path / "token"
    if not (fname_cert.exists() and fname_token.exists()):
        logit.error(f"Cannot read K8s token and secret from <{cfg.k8s_creds_path}>")
        return cfg, True

    # The K8s token is plain text but may have superfluous characters.
    token = fname_token.read_text().strip()

    # Configure the AioHTTP session with the correct K8s service account token
    # and server certificate.
    ssl_context = ssl.create_default_context(cafile=fname_cert)
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=ssl_context),
        headers={'authorization': f'Bearer {token}'},
    )

    # Duplicate the input `Config` and add the K8s session.
    cfg = Config(
        k8s_session=session,
        k8s_url=cfg.k8s_url,
        k8s_creds_path=cfg.k8s_creds_path,
    )
    return cfg, False


async def get_namespaces(sess, k8s_url: str) -> Tuple[K8sNamespaces, bool]:
    """Return all available K8s namespaces."""
    # Interrogate the K8s API about the namespaces.
    url = k8s_url + "/api/v1/namespaces"
    resp = await sess.get(url)
    if resp.status != 200:
        logit.error(f"Kubernetes responded with {resp.status} from <{url}>")
        return K8sNamespaces(namespaces=[]), True

    # Extract the list of namespace names from the response.
    data = await resp.json()
    namespaces = [_["metadata"]["name"] for _ in data["items"]]
    data = K8sNamespaces(namespaces=namespaces)
    return data, False
