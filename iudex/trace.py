from opentelemetry import trace as otel_trace
import wrapt
from typing import Callable, Any, Optional
from opentelemetry.trace import StatusCode


def trace(
    name: Optional[str] = None,
    track_args: Optional[bool] = True,
    track_kwargs: Optional[bool] = True,
    attributes: Optional[dict] = None,
) -> Callable:
    """Decorator to trace a function with OpenTelemetry, with optional span name and attributes.
    Args:
        name (Optional[str]): Optional name for the span.
        track_args (Optional[bool]): Whether to track positional arguments.
        track_kwargs (Optional[bool]): Whether to track keyword arguments.
        attributes (Optional[Dict[str, Any]]): Additional attributes to add to the span.
    """
    @wrapt.decorator
    def wrapper(wrapped: Callable, instance, args, kwargs) -> Any:
        tracer = otel_trace.get_tracer(__name__)
        with tracer.start_as_current_span(name or wrapped.__name__) as span:
            try:
                if attributes:
                    span.set_attributes(attributes)
                if track_args:
                    if len(args) == 1:
                        span.set_attribute("arg", args[0])
                    elif len(args) > 1:
                        span.set_attribute("args", args)
                if kwargs and track_kwargs:
                    span.set_attributes(kwargs)
                ret = wrapped(*args, **kwargs)
                span.set_status(StatusCode.OK)
                return ret
            except Exception as ex:
                span.set_status(StatusCode.ERROR, str(ex))
                span.record_exception(ex)
                raise ex
            finally:
                span.end()
    return wrapper


def trace_lambda(
    name: Optional[str] = None,
    track_args: Optional[bool] = True,
    attributes: Optional[dict] = None,
) -> Callable:
    """Decorator to trace a lambda function with OpenTelemetry.
    """
    return trace(name=name, track_args=track_args, attributes=attributes)

@trace()
def traced_fn():
    """Traced function"""
    return "traced"

def set_attribute(key: str, value: Any):
    """Set an attribute in the current span."""
    span = otel_trace.get_current_span()
    if span:
        span.set_attribute(key, value)
