import logging
from typing import Any, Optional, Union

try:
    from fastapi import FastAPI
except ImportError:
    FastAPI = "FastAPI"

from .instrumentation import IudexConfig, instrument
from .utils import maybe_instrument_lib

logger = logging.getLogger(__name__)


def instrument_fastapi(
    app: FastAPI = None,
    service_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    iudex_api_key: Optional[str] = None,
    log_level: Optional[Union[int, str]] = None,
    git_commit: Optional[str] = None,
    github_url: Optional[str] = None,
    env: Optional[str] = None,
    config: Optional[IudexConfig] = None,
):
    """Auto-instruments FastAPI app to send OTel signals to Iudex.

    NOTE: We recommend using `iudex.instrument` instead, which includes FastAPI.
    This function is provided to instrument a specific FastAPI app.

    Invoke this function in your FastAPI entrypoint.

    If you use Gunicorn, invoke it within a post_fork hook:
    ```python
    def post_fork(server, worker):
        instrument(...)
    ```
    Per https://opentelemetry-python.readthedocs.io/en/latest/examples/fork-process-model/README.html.

    Args:
        app: FastAPI app to instrument.
        service_name: Name of the service, e.g. "billing_service", __name__.
            If not supplied, env var OTEL_SERVICE_NAME will be used.
        instance_id: ID of the service instance, e.g. container id, pod name.
        iudex_api_key: Your Iudex API key.
            If not supplied, env var IUDEX_API_KEY will be used.
        log_level: Logging level for the root logger.
        git_commit: Commit hash of the currently deployed code.
            Used with github_url to deep link telemetry to source code.
        github_url: URL of the GitHub repository.
            Used with git_commit to deep link telemetry to source code.
        env: Environment of the service, e.g. "production", "staging".
        config: IudexConfig object with more granular options.
            Will override all other args, so provide them to the object instead.
    """
    iudex_config = instrument(
        service_name=service_name,
        instance_id=instance_id,
        iudex_api_key=iudex_api_key,
        log_level=log_level,
        git_commit=git_commit,
        github_url=github_url,
        env=env,
        config=config,
    )

    maybe_instrument_lib("opentelemetry.instrumentation.fastapi", "FastAPIInstrumentor")

    return iudex_config
