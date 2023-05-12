from fastapi import Request
from fastapi.responses import Response

import src.k8s
import src.server
from src.models import K8sNamespaces

FASTAPI_APP = src.server.FASTAPI_APP


@FASTAPI_APP.get("/k8s-namespaces", response_model=K8sNamespaces)
async def get_k8s_namespaces(request: Request, response: Response):
    """Return Kubernetes namespaces."""
    cfg = request.app.extra["config"]

    ret, err = await src.k8s.get_namespaces(cfg.k8s_session, cfg.k8s_url)
    response.status_code = 422 if err else 200
    return ret
