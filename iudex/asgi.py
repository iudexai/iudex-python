import json
import re
from typing import Any, Dict, Union
import logging

from opentelemetry.trace import Span

logger = logging.getLogger(__name__)

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

    body = message.get("body", b"")

    try:
        body_content = json.loads(body.decode("utf-8"))
        return process_dict(body_content, 0)
    except json.JSONDecodeError:
        return {"body": truncate_value(body.decode("utf-8", errors="replace"), max_value_bytes)}
    except Exception as e:
        logger.warning(f"[IUDEX] could not process request body: {e}")
        return {}

def extract_file_info(scope: Dict[str, Any], message: Dict[str, Any]) -> Dict[str, Any]:
    file_info = {}

    headers = dict(scope.get('headers', []))
    content_length = headers.get(b'content-length')
    if content_length:
        file_info['size'] = int(content_length.decode('utf-8'))

    body = message.get('body', b'')
    content_disp_match = re.search(b'filename="([^"]+)"', body[:1024])
    if content_disp_match:
        file_info['name'] = content_disp_match.group(1).decode('utf-8')

    return file_info

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
        headers = dict(scope.get('headers', []))
        content_type = headers.get(b'content-type', b'').decode('utf-8')

        if 'multipart/form-data' in content_type:
            file_info = extract_file_info(scope, message)
            if 'name' in file_info:
                span.set_attribute("http.request.file.name", file_info['name'])
            if 'size' in file_info:
                span.set_attribute("http.request.file.size", file_info['size'])
            # NOTE: semconv https://opentelemetry.io/docs/specs/semconv/attributes-registry/http/#:~:text=3495-,http.request.header.%3Ckey%3E,-string%5B%5D
            # don't directly use content_type since it includes boundary
            span.set_attribute("http.request.header.content-type", ['multipart/form-data'])
        else:
            processed_body = process_body(message)
            flattened_attrs = flatten_dict(processed_body, "http.request.body")
            for key, value in flattened_attrs.items():
                span.set_attribute(key, value)
            span.set_attribute("http.request.header.content-type", [content_type])

def client_response_hook(span: Span, scope: Dict[str, Any], message: Dict[str, Any]):
    if span and span.is_recording():
        processed_body = process_body(message)
        flattened_attrs = flatten_dict(processed_body, "http.response.body")
        for key, value in flattened_attrs.items():
            span.set_attribute(key, value)
