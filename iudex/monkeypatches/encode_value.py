import logging
from collections.abc import Sequence
from typing import Any, Mapping

import opentelemetry.exporter.otlp.proto.common._internal
from opentelemetry.proto.common.v1.common_pb2 import AnyValue as PB2AnyValue
from opentelemetry.proto.common.v1.common_pb2 import (
    ArrayValue as PB2ArrayValue,
)
from opentelemetry.proto.common.v1.common_pb2 import KeyValue as PB2KeyValue
from opentelemetry.proto.common.v1.common_pb2 import (
    KeyValueList as PB2KeyValueList,
)


def patched_encode_value(value: Any):
    if isinstance(value, bool):
        return PB2AnyValue(bool_value=value)
    if isinstance(value, str):
        return PB2AnyValue(string_value=value)
    if isinstance(value, int):
        return PB2AnyValue(int_value=value)
    if isinstance(value, float):
        return PB2AnyValue(double_value=value)
    if isinstance(value, Sequence):
        return PB2AnyValue(
            array_value=PB2ArrayValue(
                values=[patched_encode_value(v) for v in value]
            )
        )
    elif isinstance(value, Mapping):
        return PB2AnyValue(
            kvlist_value=PB2KeyValueList(
                values=[
                    patched_encode_key_value(str(k), v) for k, v in value.items()
                ]
            )
        )
    try:
        return PB2AnyValue(string_value=str(value))
    except Exception as e:
        logging.exception(e)


def patched_encode_key_value(key: str, value: Any) -> PB2KeyValue:
    return PB2KeyValue(key=key, value=patched_encode_value(value))

def monkeypatch_encode_value():
    opentelemetry.exporter.otlp.proto.common._internal._encode_value = (
        patched_encode_value
    )
    opentelemetry.exporter.otlp.proto.common._internal._encode_key_value = (
        patched_encode_key_value
    )
