import logging
import os
from typing import Optional, Union

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
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

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

IUDEX_CONFIGURED = False


class IudexConfig:
    def __init__(
        self,
        iudex_api_key: Optional[str] = None,
        service_name: Optional[str] = None,
        instance_id: Optional[str] = None,
        logs_endpoint: Optional[str] = None,
        traces_endpoint: Optional[str] = None,
        log_level: Optional[Union[str, int]] = logging.NOTSET,
    ):
        self.iudex_api_key = iudex_api_key or os.getenv("IUDEX_API_KEY")
        if not self.iudex_api_key:
            _logger.warning(
                "Missing API key, no telemetry will be sent to Iudex. "
                + "Provide the iudex_api_key parameter or set the IUDEX_API_KEY environment variable."
            )
            return

        self.service_name = (
            service_name or os.getenv(OTEL_SERVICE_NAME) or DEFAULT_SERVICE_NAME
        )
        self.instance_id = instance_id

        self.logs_endpoint = (
            logs_endpoint
            or os.getenv(OTEL_EXPORTER_OTLP_LOGS_ENDPOINT)
            or DEFAULT_IUDEX_LOGS_ENDPOINT
        )

        self.traces_endpoint = (
            traces_endpoint
            or os.getenv(OTEL_EXPORTER_OTLP_TRACES_ENDPOINT)
            or DEFAULT_IUDEX_TRACES_ENDPOINT
        )

        log_level = log_level or os.getenv(OTEL_LOG_LEVEL)
        if isinstance(log_level, str):
            log_level = LOG_LEVEL_ATOI.get(log_level.upper())
        self.log_level = log_level or logging.NOTSET

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
        if self.instance_id:
            attributes["service.instance.id"] = self.instance_id
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


def configure_logger(
    logger_name: Optional[str] = None,
    log_level: Optional[Union[str, int]] = logging.NOTSET,
):
    """Instruments a named logger.

    Useful for non-root loggers with propagate=False.
    This way, the logger still has the instrumented handler to send logs to Iudex.
    """
    if isinstance(log_level, str):
        log_level = LOG_LEVEL_ATOI.get(log_level.upper())
    log_level = log_level or logging.NOTSET

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    logger.addHandler(LoggingHandler(level=log_level))

    return logger
