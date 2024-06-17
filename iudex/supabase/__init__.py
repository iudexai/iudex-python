import logging
import os
from typing import Collection, Dict, Union

import postgrest._async.request_builder
import postgrest._sync.request_builder
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.semconv._incubating.attributes import db_attributes
from opentelemetry.semconv.attributes import http_attributes, server_attributes
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer, get_tracer
from opentelemetry.util.types import AttributeValue
from postgrest._async.request_builder import (
    AsyncQueryRequestBuilder,
    AsyncSingleRequestBuilder,
)
from postgrest._sync.request_builder import (
    SyncQueryRequestBuilder,
    SyncSingleRequestBuilder,
)
from wrapt import wrap_function_wrapper as _wrap

from .package import _instruments
from .utils import (
    parse_prefer_header_to_attributes,
    parse_sql_command,
    parse_sql_statement,
    parse_table_name,
)

logger = logging.getLogger(__name__)

_DEFAULT_SPAN_NAME_PREFIX = "supabase"
_DEFAULT_COMMAND_NAME = "request"


class SupabaseInstrumentor(BaseInstrumentor):
    def __init__(self, span_name_prefix=None):
        if not span_name_prefix:
            span_name_prefix = os.getenv(
                "OTEL_PYTHON_SUPABASE_SPAN_NAME_PREFIX",
                _DEFAULT_SPAN_NAME_PREFIX,
            )
        self._span_name_prefix = span_name_prefix.strip()

        self._should_record_statement = os.getenv("IUDEX_SHOULD_RECORD_SQL_STATEMENT", "true").lower() == "true"

        super().__init__()

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        """Instrument Supabase client.

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

        _wrap(
            postgrest._sync.request_builder,
            "SyncQueryRequestBuilder.execute",
            _wrap_execute(
                tracer,
                self._span_name_prefix,
                self._should_record_statement,
            ),
        )
        _wrap(
            postgrest._sync.request_builder,
            "SyncSingleRequestBuilder.execute",
            _wrap_execute(
                tracer,
                self._span_name_prefix,
                self._should_record_statement,
            ),
        )
        _wrap(
            postgrest._async.request_builder,
            "AsyncQueryRequestBuilder.execute",
            _wrap_execute(
                tracer,
                self._span_name_prefix,
                self._should_record_statement,
            ),
        )
        _wrap(
            postgrest._async.request_builder,
            "AsyncSingleRequestBuilder.execute",
            _wrap_execute(
                tracer,
                self._span_name_prefix,
                self._should_record_statement,
            ),
        )

    def _uninstrument(self, **kwargs):
        unwrap(SyncQueryRequestBuilder, "execute")
        unwrap(SyncSingleRequestBuilder, "execute")
        unwrap(AsyncQueryRequestBuilder, "execute")
        unwrap(AsyncSingleRequestBuilder, "execute")


def _wrap_execute(
    tracer: Tracer,
    span_name_prefix: str,
    should_record_statement: bool = True,
):
    def wrapper(
        # TODO: proper callable type from postgrest request builder
        wrapped,
        builder: Union[
            SyncQueryRequestBuilder,
            SyncSingleRequestBuilder,
            AsyncQueryRequestBuilder,
            AsyncSingleRequestBuilder,
        ],
        args,
        kwargs,
    ):
        table_name = parse_table_name(builder.path)
        url = builder.session.base_url
        http_method = builder.http_method
        params = builder.params
        headers_attributes = parse_prefer_header_to_attributes(builder.headers)
        sql_command = parse_sql_command(http_method, headers_attributes)
        body = builder.json

        span_name = " ".join(
            s
            for s in [
                span_name_prefix,
                table_name,
                sql_command or http_method or _DEFAULT_COMMAND_NAME,
            ]
            if s
        )
        span_kind = SpanKind.CLIENT

        with tracer.start_as_current_span(
            name=span_name,
            kind=span_kind,
        ) as span:
            # extract attributes from req
            if span.is_recording():
                attributes: Dict[str, AttributeValue] = {
                    db_attributes.DB_SYSTEM: "postgresql",
                }

                if table_name:
                    attributes[db_attributes.DB_SQL_TABLE] = table_name

                if sql_command:
                    attributes[db_attributes.DB_OPERATION] = sql_command
                elif http_method:
                    attributes[http_attributes.HTTP_REQUEST_METHOD] = http_method

                if url:
                    attributes[server_attributes.SERVER_ADDRESS] = str(url)

                # insert/update payload
                if body:
                    # TODO: consider setting sanitized body payload as attribute
                    logger.debug("Sending Supabase payload: %s", body)

                # where, order by, etc.
                # TODO: should be db.statement. but might be impossible to reconstruct
                if should_record_statement and params:
                    attributes[db_attributes.DB_STATEMENT] = parse_sql_statement(params)

                if headers_attributes:
                    attributes.update(headers_attributes)

                for key, value in attributes.items():
                    span.set_attribute(key, value)

            # extract attributes from res
            res = wrapped(*args, **kwargs)

            data = getattr(res, "data", None)
            error = getattr(res, "error", None)
            # NOTE: res.count is often None, so disregard
            if span.is_recording():
                if data:
                    span.set_attribute("db.num_rows", len(data))
                if error:
                    span.set_status(
                        Status(status_code=StatusCode.ERROR, description=error)
                    )

            return res

    return wrapper
