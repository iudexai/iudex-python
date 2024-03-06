import ast


def as_dict(raw_json: str) -> dict:
    """Parse raw JSON as dictionary using ast."""
    return ast.literal_eval(raw_json)
