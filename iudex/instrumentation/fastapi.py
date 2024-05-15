from typing import Optional, Union

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from .instrumentation import _IudexConfig, IudexConfig


def instrument(
    app: FastAPI,
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
        config: IudexConfig object with more granular options.
            Will override all other args, so provide them to the object instead.
    """
    config = config or {
        "iudex_api_key": iudex_api_key,
        "service_name": service_name,
        "instance_id": instance_id,
        "logs_endpoint": None,
        "traces_endpoint": None,
        "log_level": log_level,
        "git_commit": git_commit,
        "github_url": github_url,
        "env": env,
    }
    iudex_config = _IudexConfig(**config)

    iudex_config.configure()
    FastAPIInstrumentor().instrument_app(app)

    return iudex_config
