import importlib.util
import logging
from typing import Optional, Union

from .config import IudexConfig, _IudexConfig

logger = logging.getLogger(__name__)


def instrument(
    service_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    iudex_api_key: Optional[str] = None,
    log_level: Optional[Union[int, str]] = None,
    git_commit: Optional[str] = None,
    github_url: Optional[str] = None,
    env: Optional[str] = None,
    config: Optional[IudexConfig] = None,
):
    """Auto-instruments app to send OTel signals to Iudex.

    Invoke this function in your app entrypoint.

    Args:
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

    _instrument_openai()
    _instrument_supabase()
    _instrument_sqlalchemy()

    return iudex_config


def _instrument_openai():
    try:
        if importlib.util.find_spec("openai") is None:
            return
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        instrumentor = OpenAIInstrumentor(
            enrich_assistant=True,
            enrich_token_usage=True,
            exception_logger=logger.error,
        )
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument()
    except Exception as e:
        logger.exception(f"Failed to instrument OpenAI: {e}")

def _instrument_supabase():
    try:
        if importlib.util.find_spec("supabase") is None:
            return
        if importlib.util.find_spec("postgrest") is None:
            return
        from .supabase import SupabaseInstrumentor
        instrumentor = SupabaseInstrumentor()
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument()
    except Exception as e:
        logger.exception(f"Failed to instrument Supabase: {e}")

def _instrument_sqlalchemy():
    try:
        if importlib.util.find_spec("sqlalchemy") is None:
            return
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        instrumentor = SQLAlchemyInstrumentor()
        if not instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.instrument(enable_commenter=True)
    except Exception as e:
        logger.exception(f"Failed to instrument SQLAlchemy: {e}")
