import logging
import os
from typing import Collection, Dict, Union

from django.db.models import Model, QuerySet
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.semconv._incubating.attributes import db_attributes
from opentelemetry.semconv.attributes import http_attributes, server_attributes
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer, get_tracer
from opentelemetry.util.types import AttributeValue
from wrapt import wrap_function_wrapper as _wrap

from .package import _instruments
from .utils import (
    queryset_methods_to_patch,
    model_methods_to_patch,
)

logger = logging.getLogger(__name__)

class DjangoInstrumentor(BaseInstrumentor):
    def __init__(self):
        super().__init__()

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        """Instrument Django client.

        Args:
            tracer_provider: The `TracerProvider` to use. If none is passed the
                current configured one is used.
        """
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            instrumenting_module_name=__name__,
            instrumenting_library_version=None,
            tracer_provider=tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.11.0",
        )

        for method_name in queryset_methods_to_patch:
            _wrap(
                QuerySet,
                method_name,
                _wrap_queryset(tracer),
            )

        for method_name in model_methods_to_patch:
            _wrap(
                Model,
                method_name,
                _wrap_model(tracer),
            )

    def _uninstrument(self, **kwargs):
        for method_name in queryset_methods_to_patch:
            unwrap(QuerySet, method_name)
        for method_name in model_methods_to_patch:
            unwrap(Model, method_name)


def _wrap_queryset(tracer: Tracer):
    def wrapper(wrapped: callable, instance: QuerySet, args: tuple, kwargs: dict):
        span_name = f"django.{instance.model.__name__}.{wrapped.__name__}"
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute('db.collection.name', instance.model.__name__)
            try: 
                res = wrapped(*args, **kwargs)
                span.set_status(StatusCode.OK)
                return res
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise e
    return wrapper

def _wrap_model(tracer: Tracer):
    def wrapper(wrapped: callable, instance: Model, args: tuple, kwargs: dict):
        try:
            span_name = f"django.{instance.__class__.__name__}.{wrapped.__name__}"
        except Exception as e:
            raise e
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute('db.collection.name', instance.__class__.__name__)
            try: 
                res = wrapped(*args, **kwargs)
                span.set_status(StatusCode.OK)
                return res
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise e
    return wrapper