import logging
import os
import sys
from pathlib import Path

import uvicorn
from prometheus_client import start_http_server

import src.endpoints
import src.logstreams
import src.server
from src.models import Config

# Convenience.
logit = logging.getLogger("app")


def main() -> int:
    """Validate the configuration and start the server process.

    Return a non-zero exit code if the server did not shut down cleanly.

    """
    # Setup JSON logging.
    log_level = os.environ.get("log_level", "info")
    src.logstreams.setup(log_level)
    logit.info("Bootstrapping server")

    # Convenience.
    app = src.server.FASTAPI_APP

    # Populate a Config structure and add it to the global FastAPI application
    # variable . Abort immediately if any of the mandatory environment
    # variables is missing.
    try:
        app.extra["config"] = Config(
            # Placeholder. Will be populated during server startup.
            k8s_session=None,

            # K8s will automatically inject this into the Pod.
            k8s_url="https://" + os.environ["KUBERNETES_SERVICE_HOST"],

            # Manifest must specify this environment variable explicitly.
            k8s_creds_path=Path(os.environ["K8S_CREDENTIALS_PATH"]),
        )
    except KeyError as e:
        logit.critical(f"Environment variable <{e.args[0]}> is undefined")
        return 1

    # Start the web server.
    uvicorn.run(
        # Specify the FastAPI application to run.
        app=app,
        host="0.0.0.0",
        port=8080,
        log_level=log_level,

        # Disable access logs.
        access_log=False,

        # Force `uvicorn` to use our own log streams and thus produce JSON
        # formatted output.
        log_config=None,
    )

    # We only get here if the server shut down cleanly, most likely because
    # it received a SIGTERM signal.
    logit.info("Shutdown complete")
    return 0


if __name__ == '__main__':      # codecov-skip
    start_http_server(port=8081, addr="0.0.0.0")
    sys.exit(main())
