import src.server

FASTAPI_APP = src.server.FASTAPI_APP


@FASTAPI_APP.get("/healthz")
async def get_healthz():
    """Kubernetes health check endpoint."""
    return ""
