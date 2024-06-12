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
    attributes = flatten_attributes(record)

    # Add standard code attributes for logs.
    attributes[SpanAttributes.CODE_FILEPATH] = record.pathname
    attributes[SpanAttributes.CODE_FUNCTION] = record.funcName
    attributes[SpanAttributes.CODE_LINENO] = record.lineno

    if record.exc_info:
        exctype, value, tb = record.exc_info
        if exctype is not None:
            attributes[SpanAttributes.EXCEPTION_TYPE] = exctype.__name__
        if value is not None and value.args:
            attributes[SpanAttributes.EXCEPTION_MESSAGE] = str(value.args[0])
        if tb is not None:
            # https://github.com/open-telemetry/opentelemetry-specification/blob/9fa7c656b26647b27e485a6af7e38dc716eba98a/specification/trace/semantic_conventions/exceptions.md#stacktrace-representation
            attributes[SpanAttributes.EXCEPTION_STACKTRACE] = "".join(
                traceback.format_exception(*record.exc_info)
            )
    return attributes


def flatten_attributes(record: LogRecord):
    """Convert LogRecord to flattened attribute dict.

    For instance {"a": {"b": 1}} will be converted to {"a.b": 1}.
    """
    seen = set()
    attrs = {}
    def flatten_helper(item, prefix=""):
        if prefix in _RESERVED_ATTRS:
            return
        if not isinstance(item, dict):
            attrs[prefix] = str(item)
            return
        for key, value in item.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if id(value) in seen:
                # circular reference
                attrs[full_key] = str(value)
                continue
            seen.add(id(value))
            flatten_helper(value, full_key)
            seen.remove(id(value))
    flatten_helper(vars(record))
    return attrs
