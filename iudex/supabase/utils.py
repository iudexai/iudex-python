import logging
from typing import Dict, Literal, Optional

from httpx import Headers, QueryParams
from opentelemetry.util.types import AttributeValue

logger = logging.getLogger(__name__)

SqlCommand = Literal["SELECT", "INSERT", "UPDATE", "UPSERT", "DELETE"]

PARAM_TO_OPERATOR = {
    "eq": "eq",
    "neq": "neq",
    "gt": "gt",
    "gte": "gte",
    "lt": "lt",
    "lte": "lte",
    "like": "like",
    "ilike": "ilike",
    "is": "is_",
    "in": "in_",
    "cs": "contains",
    "cd": "contained_by",
    "match": "match",
    "not": "not_",
    # below are not used by supabase
    "imatch": "imatch",
    "isdistinct": "isdistinct",
    "fts": "fts",
    "plfts": "plfts",
    "phfts": "phfts",
    "wfts": "wfts",
    "ov": "ov",
    "sl": "sl",
    "sr": "sr",
    "nxr": "nxr",
    "nxl": "nxl",
    "adj": "adj",
    "or": "or",
    "and": "and",
    "all": "all",
    "any": "any",
}


def parse_table_name(path: str) -> Optional[str]:
    """Naively parse table name from Supabase path.

    Args:
        path: Request path, e.g. /my_table
    """
    try:
        return path.split("/")[1]
    except Exception as e:
        logger.exception("Failed to extract table name from path %s: %s", path, e)


def parse_sql_command(
    http_method: str, headers_attributes: Dict[str, AttributeValue]
) -> Optional[SqlCommand]:
    """Parse SQL command from Supabase request.

    Args:
        http_method: HTTP method, e.g. GET, POST, PUT, PATCH, DELETE
        headers_attributes: Parsed headers as attributes dict
    """
    if http_method == "GET" or http_method == "HEAD":
        return "SELECT"
    elif http_method == "POST":
        if (
            headers_attributes.get("http.header.prefer.resolution")
            == "merge-duplicates"
        ):
            return "UPSERT"
        return "INSERT"
    elif http_method == "PUT":
        return "UPSERT"
    elif http_method == "PATCH":
        return "UPDATE"
    elif http_method == "DELETE":
        return "DELETE"

    logger.exception(
        "Failed to parse SQL command from http method %s, headers %s",
        http_method,
        headers_attributes,
    )


def parse_prefer_header_to_attributes(headers: Headers) -> Dict[str, AttributeValue]:
    """Parse headers into OTel compliant attributes dict.

    Uses HTTP semconv.
    See https://opentelemetry.io/docs/specs/semconv/attributes-registry/http/#http-attributes.

    Also parses nested Prefer headers, e.g. Prefer: resolution=merge-duplicates
    See https://www.rfc-editor.org/rfc/rfc7240.html.

    Args:
        headers: HTTP headers
    """
    attributes = {}
    for key, value in headers.items():
        if key.lower() == "authorization":
            continue
        if key.lower() == "prefer":
            for prefer in value.split(","):
                prefer_key, prefer_value = prefer.split("=")
                attributes[f"http.header.prefer.{prefer_key}"] = prefer_value
            continue
        attributes[f"http.header.{key}"] = value
    return attributes


def parse_sql_statement(params: QueryParams) -> str:
    """Parse pseudo SQL statement from Supabase request params.

    See https://postgrest.org/en/v12/references/api/tables_views.html#operators

    We naively return the params in a syntax more similar to Supabase ORM than SQL.

    Ideally, we would start a span when the query begins building, monkey patch every
    subsequent query builder method, and collect the args as they are passed in.

    Args:
        params: Request params
    """
    statements = []
    for key, value in params.items():
        op = value.split(".")[0]
        if op in PARAM_TO_OPERATOR:
            statements.append(f".{PARAM_TO_OPERATOR[op]}({key}, {value[len(op) + 1:]})")
            continue
        statements.append(f".{key}({value})")
    return "".join(statements)
