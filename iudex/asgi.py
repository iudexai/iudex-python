import json
from typing import Any, Dict, Union

from opentelemetry.trace import Span


def process_body(
    message: Dict[str, Any],
    # TODO: configurable
    max_keys: int = 32,
    max_depth: int = 4,
    max_value_bytes: int = 1024,
) -> Dict[str, Any]:
    def process_value(value: Any, current_depth: int) -> Union[str, Dict, list]:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return truncate_value(str(value), max_value_bytes)
        elif isinstance(value, dict):
            return process_dict(value, current_depth + 1)
        elif isinstance(value, list):
            return [process_value(item, current_depth + 1) for item in value[:max_keys]]
        else:
            return truncate_value(str(value), max_value_bytes)

    def process_dict(d: Dict[str, Any], current_depth: int) -> Dict[str, Any]:
        result = {}
        for i, (key, value) in enumerate(d.items()):
            if i >= max_keys:
                result["..."] = f"exceeded max_keys of {max_keys}"
                break
            if current_depth >= max_depth:
                result[key] = truncate_value(str(value), max_value_bytes)
            else:
                result[key] = process_value(value, current_depth)
        return result

    def truncate_value(value: str, max_bytes: int) -> str:
        encoded = value.encode("utf-8")
        if len(encoded) > max_bytes:
            truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
            return f"{truncated}... (max_value_bytes of {max_bytes} exceeded)"
        return value

    # Extract and process the body according to ASGI spec
    body = message.get("body", b"")
    more_body = message.get("more_body", False)

    # Accumulate body chunks if more_body is True
    while more_body:
        # In a real scenario, you'd need to await the next message
        # This is a simplified version
        next_message = {}  # This should be the next message in the ASGI cycle
        body += next_message.get("body", b"")
        more_body = next_message.get("more_body", False)

    # Try to parse body as JSON, fall back to string if it fails
    try:
        body_content = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        body_content = body.decode("utf-8", errors="replace")

    if isinstance(body_content, dict):
        return process_dict(body_content, 0)
    else:
        return {"body": truncate_value(str(body_content), max_value_bytes)}


def flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    items = []
    for k, v in d.items():
        new_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key).items())
        elif isinstance(v, (str, int, float, bool)) or v is None:
            items.append((new_key, v))
        else:
            items.append((new_key, json.dumps(v)))
    return dict(items)


def client_request_hook(span: Span, scope: Dict[str, Any], message: Dict[str, Any]):
    if span and span.is_recording():
        processed_body = process_body(message)
        flattened_attrs = flatten_dict(processed_body, "http.request.body")
        for key, value in flattened_attrs.items():
            span.set_attribute(key, value)


def client_response_hook(span: Span, scope: Dict[str, Any], message: Dict[str, Any]):
    if span and span.is_recording():
        processed_body = process_body(message)
        flattened_attrs = flatten_dict(processed_body, "http.response.body")
        for key, value in flattened_attrs.items():
            span.set_attribute(key, value)
