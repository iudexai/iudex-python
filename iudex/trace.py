import functools
from typing import Callable, Any, Optional

import wrapt
from opentelemetry import trace as otel_trace
from opentelemetry.trace import StatusCode


def trace(
    wrapped: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    ignore_args: Optional[bool] = None,
    ignore_kwargs: Optional[bool] = None,
    attributes: Optional[dict] = None,
) -> Callable:
    """Decorator to trace a function with OpenTelemetry.

    Args:
        name (Optional[str]): Optional span name. Defaults to the wrapped function's name.
        ignore_args (Optional[bool]): Whether to ignore positional arguments, tracking is one default.
        ignore_kwargs (Optional[bool]): Whether to ignore keyword arguments, tracking is on by default.
        attributes (Optional[Dict[str, Any]]): Additional attributes to add to the span.
    """
    if wrapped is None:
        return functools.partial(
            trace,
            name=name,
            ignore_args=ignore_args,
            ignore_kwargs=ignore_kwargs,
            attributes=attributes,
        )

    @wrapt.decorator
    def wrapper(wrapped: Callable, instance, args, kwargs) -> Any:
        tracer = otel_trace.get_tracer(__name__)
        with tracer.start_as_current_span(name or wrapped.__name__) as span:
            try:
                if attributes:
                    span.set_attributes(attributes)

                if args and not ignore_args:
                    if len(args) == 1:
                        span.set_attribute("arg", args[0])
                    elif len(args) > 1:
                        span.set_attribute("args", args)
                if kwargs and not ignore_kwargs:
                    span.set_attributes(kwargs)

                ret = wrapped(*args, **kwargs)

                span.set_status(StatusCode.OK)
                return ret
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise e

    return wrapper(wrapped)  # type: ignore


def trace_lambda(
    name: Optional[str] = None,
    ignore_args: Optional[bool] = None,
    attributes: Optional[dict] = None,
) -> Callable:
    """Decorator to trace a lambda function with OpenTelemetry."""
    return trace(name=name, ignore_args=ignore_args, attributes=attributes)


def set_attribute(key: str, value: Any):
    """Set an attribute in the current span."""
    span = otel_trace.get_current_span()
    if span:
        span.set_attribute(key, value)
