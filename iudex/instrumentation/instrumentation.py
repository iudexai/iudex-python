import logging
import os
from typing import Optional, TypedDict, Union
import subprocess

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.environment_variables import (
    OTEL_EXPORTER_OTLP_HEADERS,
    OTEL_EXPORTER_OTLP_LOGS_ENDPOINT,
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
    OTEL_LOG_LEVEL,
    OTEL_SERVICE_NAME,
)
from opentelemetry.sdk.resources import Resource, Attributes
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

from .attributes import get_attributes

_logger = logging.getLogger(__name__)

DEFAULT_SERVICE_NAME = "unknown_service:python"
DEFAULT_IUDEX_LOGS_ENDPOINT = "https://api.iudex.ai/resource_logs"
DEFAULT_IUDEX_TRACES_ENDPOINT = "https://api.iudex.ai/traces"
LOG_LEVEL_ATOI = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "NOTSET": logging.NOTSET,
}
DEFAULT_LOG_LEVEL = logging.INFO

IUDEX_CONFIGURED = False


class IudexConfig(TypedDict, total=False):
    iudex_api_key: Optional[str]
    service_name: Optional[str]
    instance_id: Optional[str]
    logs_endpoint: Optional[str]
    traces_endpoint: Optional[str]
    log_level: Optional[Union[str, int]]
    git_commit: Optional[str]
    github_url: Optional[str]
    env: Optional[str]
    attributes: Optional[Attributes]


class _IudexConfig:
    def __init__(
        self,
        **kwargs,
    ):
        self.iudex_api_key = kwargs["iudex_api_key"] or os.getenv("IUDEX_API_KEY")
        if not self.iudex_api_key:
            _logger.warning(
                "Missing API key, no telemetry will be sent to Iudex. "
                + "Provide the iudex_api_key parameter or set the IUDEX_API_KEY environment variable."
            )
            return

        self.service_name = (
            kwargs["service_name"]
            or os.getenv(OTEL_SERVICE_NAME)
            or DEFAULT_SERVICE_NAME
        )
        self.instance_id = kwargs["instance_id"]

        self.logs_endpoint = (
            kwargs["logs_endpoint"]
            or os.getenv(OTEL_EXPORTER_OTLP_LOGS_ENDPOINT)
            or DEFAULT_IUDEX_LOGS_ENDPOINT
        )

        self.traces_endpoint = (
            kwargs["traces_endpoint"]
            or os.getenv(OTEL_EXPORTER_OTLP_TRACES_ENDPOINT)
            or DEFAULT_IUDEX_TRACES_ENDPOINT
        )

        log_level = kwargs["log_level"] or os.getenv(OTEL_LOG_LEVEL)
        if isinstance(log_level, str):
            log_level = LOG_LEVEL_ATOI.get(log_level.upper())
        self.log_level = log_level or DEFAULT_LOG_LEVEL

        self.git_commit = kwargs["git_commit"] or os.getenv("GIT_COMMIT")
        if not self.git_commit:
            try:
                self.git_commit = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"]
                ).strip()
            except:
                pass

        self.github_url = kwargs["github_url"] or os.getenv("GITHUB_URL")

        self.env = kwargs["env"] or os.getenv("ENV") or os.getenv("ENVIRONMENT")

        self.attributes = kwargs.get("attributes", {})

    def configure(self):
        if not self.iudex_api_key:
            _logger.warning(
                "Missing API key, no telemetry will be sent to Iudex. "
                + "Provide the iudex_api_key parameter or set the IUDEX_API_KEY environment variable."
            )
            return

        global IUDEX_CONFIGURED
        if IUDEX_CONFIGURED:
            return

        # configure common
        attributes = {}
        attributes["service.name"] = self.service_name
        attributes["service.instance.id"] = self.instance_id
        attributes["git.commit"] = self.git_commit
        attributes["github.url"] = self.github_url
        attributes["env"] = self.env
        # clean attributes
        attributes = {
            key: value for key, value in attributes.items() if value is not None
        }

        # add manual attributes
        attributes.update(self.attributes)

        # create resource
        resource = Resource.create(attributes)

        # set default headers to send iudex api key
        headers = {"x-api-key": self.iudex_api_key}
        os.environ[OTEL_EXPORTER_OTLP_HEADERS] = f"x-api-key:{self.iudex_api_key}"

        # configure logger
        logger_provider = LoggerProvider(resource=resource)
        log_exporter = OTLPLogExporter(endpoint=self.logs_endpoint, headers=headers)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        set_logger_provider(logger_provider)
        logging.basicConfig(level=self.log_level)
        # add handler to root logger
        configure_logger(log_level=self.log_level)

        # configure tracer
        trace_provider = TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=self.traces_endpoint, headers=headers)
        trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        set_tracer_provider(trace_provider)

        IUDEX_CONFIGURED = True


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

    Invoke this function in your Lambda entrypoint.

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

    return iudex_config


def configure_logger(
    logger_name: Optional[str] = None,
    log_level: Optional[Union[str, int]] = None,
):
    """Instruments a named logger.

    Useful for non-root loggers with propagate=False.
    This way, the logger still has the instrumented handler to send logs to Iudex.
    """
    if isinstance(log_level, str):
        log_level = LOG_LEVEL_ATOI.get(log_level.upper())
    log_level = log_level or DEFAULT_LOG_LEVEL

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    logger_handler = LoggingHandler(level=log_level)
    logger_handler._get_attributes = get_attributes
    logger.addHandler(logger_handler)

    return logger
