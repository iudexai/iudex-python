import traceback
from logging import LogRecord
from typing import Dict

from opentelemetry.semconv.trace import SpanAttributes

# skip natural LogRecord attributes
# http://docs.python.org/library/logging.html#logrecord-attributes
_RESERVED_ATTRS = frozenset(
    (
        "asctime",
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "message",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    )
)


def get_attributes(record: LogRecord):
    """Monkeypatch for non-primitive (e.g. dict) attribute values defined in LogRecord.extra.

    See https://github.com/open-telemetry/opentelemetry-python/blob/c06e6f4b8616618907d70fa023eb2baab7a6ca61/opentelemetry-sdk/src/opentelemetry/sdk/_logs/_internal/__init__.py#L460
    """
    attributes: Dict = {
        k: str(v) for k, v in vars(record).items() if k not in _RESERVED_ATTRS
    }

    # Add standard code attributes for logs.
    attributes[SpanAttributes.CODE_FILEPATH] = record.pathname
    attributes[SpanAttributes.CODE_FUNCTION] = record.funcName
    attributes[SpanAttributes.CODE_LINENO] = record.lineno

    if record.exc_info:
        exctype, value, tb = record.exc_info
        if exctype is not None:
            attributes[SpanAttributes.EXCEPTION_TYPE] = exctype.__name__
        if value is not None and value.args:
            attributes[SpanAttributes.EXCEPTION_MESSAGE] = value.args[0]
        if tb is not None:
            # https://github.com/open-telemetry/opentelemetry-specification/blob/9fa7c656b26647b27e485a6af7e38dc716eba98a/specification/trace/semantic_conventions/exceptions.md#stacktrace-representation
            attributes[SpanAttributes.EXCEPTION_STACKTRACE] = "".join(
                traceback.format_exception(*record.exc_info)
            )
    return attributes
