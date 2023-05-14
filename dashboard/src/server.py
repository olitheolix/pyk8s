import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import src
import src.k8s
import src.main
import src.metrics

# Convenience.
logit = logging.getLogger("app")


# The FastAPI server instance.
FASTAPI_APP = FastAPI(
    title="Dashboard App",
    description="Dashboard App",
    version=src.__version__,
    contact={
        "name": "Oliver Nagy",
        "email": "olitheolix@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


@FASTAPI_APP.on_event("startup")
async def startup_event():
    """Server startup."""
    # Create the K8s session. Use a hard abort if that fails.
    cfg, err = src.k8s.create_session(FASTAPI_APP.extra["config"])
    assert not err

    FASTAPI_APP.extra["config"] = cfg

    logit.info("Bootstrapping complete")


@FASTAPI_APP.on_event("shutdown")
async def shutdown_event():
    """Server shutdown."""
    logit.info("shutting down")

    # Close the K8s session.
    session = FASTAPI_APP.extra["config"].k8s_session
    await session.close()
    logit.info("shutdown complete")


@FASTAPI_APP.middleware("http")
async def middleware(request: Request, call_next):
    """Track access requests with Prometheus counter."""
    try:
        response = await call_next(request)
    except Exception:
        logit.exception("An exception occurred")
        return JSONResponse(
            status_code=418,
            content={"message": f"Oops! There goes a rainbow..."},
        )

    # Count the request by path.
    metric = src.metrics.PROM_REQ_CNT
    metric.labels(request.method, request.url.path, response.status_code).inc(1)
    return response
