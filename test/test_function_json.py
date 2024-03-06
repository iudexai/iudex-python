import pytest
from openai.types.chat.completion_create_params import Function as OpenAiFunction
from pydantic import ValidationError

from iudex.types.function import FunctionJson


def test_successful_validation():
    """Test that a correctly shaped dictionary passes validation."""
    schema = {
        "name": "getCurrentWeather",
        "description": "Gets the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get the weather for",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
        "returns": {
            "type": "object",
            "properties": {
                "temperature": {
                    "description": "The temperature value.",
                    "type": "number",
                },
                "temperatureUnit": {
                    "description": "The temperature unit.",
                    "type": "number",
                },
                "windSpeed": {
                    "description": "The wind speed in miles per hour.",
                    "type": "number",
                },
                "shortForecast": {
                    "description": "A short description of the forecast.",
                    "type": "string",
                },
            },
        },
    }

    try:
        FunctionJson(**schema)
    except ValidationError as e:
        pytest.fail(f"Unexpected ValidationError: {e}")


def test_failure_due_to_invalid_payload():
    """Test that an invalid dictionary fails validation with detailed feedback."""
    schema = {
        "name": "getCurrentWeatherMultiple",
        "description": "Gets the current weather for multiple locations",
        "parameters": {
            "type": "object",
            "properties": {
                "locations": {
                    "type": "array",
                    "description": "string",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
    with pytest.raises(ValidationError) as exc_info:
        FunctionJson(**schema)

    is_missing_items = False
    is_missing_returns = False

    errors = exc_info.value.errors()
    for e in errors:
        if e["loc"] == ("parameters", "items"):
            is_missing_items = True
        if e["loc"] == ("returns",):
            is_missing_returns = True

    assert is_missing_items
    assert is_missing_returns


def test_convert_from_openai_function():
    """Test that an OpenAI function can be converted to an Iudex function."""
    openai_function: OpenAiFunction = {
        "name": "getCurrentWeather",
        "description": "Gets the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get the weather for",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
    returns = {
        "type": "object",
        "properties": {
            "temperature": {
                "description": "The temperature value.",
                "type": "number",
            },
            "temperatureUnit": {
                "description": "The temperature unit.",
                "type": "number",
            },
            "windSpeed": {
                "description": "The wind speed in miles per hour.",
                "type": "number",
            },
            "shortForecast": {
                "description": "A short description of the forecast.",
                "type": "string",
            },
        },
    }
    usage_example = "getCurrentWeather({location: 'New York', unit: 'celsius'})"
    returns_example = (
        '{"temperature": 20, "temperatureUnit": "celsius", "windSpeed": 10, "shortForecast": "Sunny"}'
    )
    function = FunctionJson.from_openai_function(
        openai_function, returns, usage_example, returns_example
    )
    assert function.name == "getCurrentWeather"
    assert function.description == "Gets the current weather"
    assert function.parameters.dict() == openai_function["parameters"]
    assert function.returns.dict() == returns
    assert function.usageExample == usage_example
    assert function.returnsExample == returns_example
