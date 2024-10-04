# ruff: noqa: E402
# ^ because monkeypatches must import and run before other imports
from .monkeypatches.get_attributes import patched_get_attributes
from .monkeypatches.logging import monkeypatch_LogRecord_getMessage
from .monkeypatches.print import monkeypatch_print

import importlib.util
import logging
import os
import re
import subprocess
from typing import Callable, Optional, TypedDict, Union
import secrets

from opentelemetry.sdk.trace.id_generator import IdGenerator
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler, LogRecordProcessor, LogData, LogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.environment_variables import (
    OTEL_EXPORTER_OTLP_HEADERS,
    OTEL_EXPORTER_OTLP_LOGS_ENDPOINT,
    OTEL_EXPORTER_OTLP_TIMEOUT,
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
    OTEL_LOG_LEVEL,
    OTEL_SERVICE_NAME,
)
from opentelemetry.sdk.resources import Attributes, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

_logger = logging.getLogger(__name__)

DEFAULT_SERVICE_NAME = "unknown_service:python"
DEFAULT_IUDEX_LOGS_ENDPOINT = "https://api.iudex.ai/resource_logs"
DEFAULT_IUDEX_TRACES_ENDPOINT = "https://api.iudex.ai/traces"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_TIMEOUT = 60

LOG_LEVEL_ATOI = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "NOTSET": logging.NOTSET,
}

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
    timeout: Optional[int]
    disable_print: Optional[bool]
    redact: Optional[Union[str, re.Pattern, Callable[[LogRecord], None]]]


class _IudexConfig:
    def __init__(
        self,
        **kwargs: IudexConfig,
    ):
        self.iudex_api_key = kwargs.get("iudex_api_key") or os.getenv("IUDEX_API_KEY")
        if not self.iudex_api_key:
            _logger.warning(
                "Missing API key, no telemetry will be sent to Iudex. "
                + "Provide the iudex_api_key parameter or set the IUDEX_API_KEY environment variable."
            )
            return

        self.service_name = (
            kwargs.get("service_name")
            or os.getenv(OTEL_SERVICE_NAME)
            or DEFAULT_SERVICE_NAME
        )
        self.instance_id = kwargs.get("instance_id")

        self.logs_endpoint = (
            kwargs.get("logs_endpoint")
            or os.getenv(OTEL_EXPORTER_OTLP_LOGS_ENDPOINT)
            or DEFAULT_IUDEX_LOGS_ENDPOINT
        )

        self.traces_endpoint = (
            kwargs.get("traces_endpoint")
            or os.getenv(OTEL_EXPORTER_OTLP_TRACES_ENDPOINT)
            or DEFAULT_IUDEX_TRACES_ENDPOINT
        )

        log_level = kwargs.get("log_level") or os.getenv(OTEL_LOG_LEVEL)
        if isinstance(log_level, str):
            log_level = LOG_LEVEL_ATOI.get(log_level.upper())
        self.log_level = log_level or DEFAULT_LOG_LEVEL

        self.git_commit = kwargs.get("git_commit") or os.getenv("GIT_COMMIT")
        if not self.git_commit:
            try:
                self.git_commit = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"]
                ).strip()
            except:
                pass

        self.github_url = kwargs.get("github_url") or os.getenv("GITHUB_URL")

        self.env = kwargs.get("env") or os.getenv("ENV") or os.getenv("ENVIRONMENT")

        self.attributes = kwargs.get("attributes", {})

        self._timeout = kwargs.get("timeout") or int(os.getenv(OTEL_EXPORTER_OTLP_TIMEOUT, DEFAULT_TIMEOUT))

        self.disable_print = kwargs.get("disablePrint") or kwargs.get("disable_print") or False

        self.redact = kwargs.get("redact") or None

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
        os.environ[OTEL_EXPORTER_OTLP_HEADERS] = f"x-api-key={self.iudex_api_key}"

        # configure logger
        logger_provider = LoggerProvider(resource=resource)
        log_exporter = OTLPLogExporter(endpoint=self.logs_endpoint, headers=headers, timeout=self._timeout)
        if self.redact:
            logger_provider.add_log_record_processor(RedactLogProcessor(self.redact))
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        set_logger_provider(logger_provider)
        logging.basicConfig(level=self.log_level)
        # add otel handler to root logger
        configure_logging(log_level=self.log_level)
        if not self.disable_print: 
            # monkeypatch print to emit with otel handler
            monkeypatch_print(LoggingHandler(level=logging.INFO))

        # configure tracer
        trace_provider = TracerProvider(resource=resource, id_generator=IudexIdGenerator())
        span_exporter = OTLPSpanExporter(endpoint=self.traces_endpoint, headers=headers, timeout=self._timeout)
        trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        set_tracer_provider(trace_provider)

        IUDEX_CONFIGURED = True


def configure_logging(
    logger_name: Optional[str] = None,
    log_level: Optional[Union[str, int]] = None,
):
    monkeypatch_LogRecord_getMessage()

    logger_handler = LoggingHandler(level=log_level)
    logger_handler._get_attributes = patched_get_attributes

    configure_logger(
        logger_name=logger_name, log_level=log_level, logger_handler=logger_handler
    )
    configure_loguru(log_level=log_level, logger_handler=logger_handler)

def configure_logger(
    logger_name: Optional[str] = None,
    log_level: Optional[Union[str, int]] = None,
    logger_handler: Optional[LoggingHandler] = None,
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

    if not logger_handler:
        logger_handler = LoggingHandler(level=log_level)
        logger_handler._get_attributes = patched_get_attributes

    logger.addHandler(logger_handler)

    return logger


def configure_loguru(
    log_level: Optional[Union[str, int]] = None,
    logger_handler: Optional[LoggingHandler] = None,
    format: Optional[str] = None,
):
    """Instruments Loguru to send logs to Iudex."""
    if importlib.util.find_spec("loguru") is None:
        return
    from loguru import logger

    if isinstance(log_level, str):
        log_level = LOG_LEVEL_ATOI.get(log_level.upper())
    log_level = log_level or DEFAULT_LOG_LEVEL

    if not logger_handler:
        logger_handler = LoggingHandler(level=log_level)
        logger_handler._get_attributes = patched_get_attributes

    if not format:
        format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"

    logger.add(logger_handler, format=format)

    return logger

class RedactLogProcessor(LogRecordProcessor):
    def __init__(
        self,
        redact: Union[str, re.Pattern, Callable[[LogRecord], None]],
    ):
        self.redact = redact
        if callable(redact):
            self.redact_fn = redact
        elif isinstance(redact, str):
            def redact_fn(record: LogRecord) -> str:
                if isinstance(record.body, str):
                    record.body = re.sub(redact, "REDACTED", record.body)
            self.redact_fn = redact_fn

    def emit(self, log_data: LogData):
        if self.redact_fn:
            self.redact_fn(log_data.log_record)
    
    def shutdown(self):
        pass

    def force_flush(self, timeout_millis: int = 30000):
        return True

class IudexIdGenerator(IdGenerator):
    def generate_span_id(self) -> int:
        return secrets.randbits(64)
    def generate_trace_id(self) -> int:
        return secrets.randbits(128)
