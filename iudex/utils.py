def clean_json(raw_json: str) -> str:
    """Clean up raw JSON body for parsing."""
    return raw_json.replace("'", '"').replace("None", '"null"')
