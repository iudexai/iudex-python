# Iudex Python Client SDK

**Easily build 🛠️ natural language interfaces for ✨ your own ✨ applications 💻**

[Iudex](https://iudex.ai) is an API layer that allows you to quickly build applications that can use LLM reasoning in a way that is more
accurate, secure, and scalable than the toy examples from other projects. Iudex does this by providing an out-of-the-box
LLM orchestration architecture capable of working with millions of functions and documents.

**❗ Leverage the power 🦾 of LLMs 🤖 with Iudex ❗**

## Installation

```bash
pip install iudex
```

## How It Works

Iudex works by first indexing your functions. Afterwards, when making a query, Iudex will figure out the best way to accomplish that query
by intelligently sequencing the functions you have connected and with the prebuilt functions we have created. This way, Iudex ensures
that the functions that get called do not suffer from hallucinations and can properly use the results from previously run functions.

## Usage Example

See more examples in the `examples` directory.

Before running examples, make sure to set the `IUDEX_API_KEY` environment variable or pass your API key directly to the `Iudex` constructor.

Visit [iudex.ai](https://iudex.ai) to Sign Up and receive an API key.

```python
from iudex import Iudex

client = Iudex()

get_current_weather_spec = {
    "name": "get_current_weather",
    "description": "Gets the current weather",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g., San Francisco, CA",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The temperature unit",
            },
        },
        "required": ["location"],
    },
    "returns": {
        "type": "object",
        "properties": {
            "temp": {
                "type": "number",
                "description": "The temperature value",
            },
            "unit": {
                "type": "string",
                "description": "The temperature unit",
            },
        },
    },
}


def get_current_weather(location: str, unit="fahrenheit"):
    print(f"Getting weather for {location} in {unit}...\n")
    temp = 70
    if unit == "celsius":
        temp = temp // 2
    return {
        "temp": temp,
        "unit": unit,
    }


def upload_and_link_functions():
    print("Uploading functions...\n")
    functions = [get_current_weather_spec]
    client.functions.upsert(functions=functions, module="weather_module")

    print("Linking functions...\n")

    def function_linker(name: str):
        if name == "get_current_weather":
            return get_current_weather

    client.link_functions(function_linker)


def run_weather_chatbot():
    req_msg = "What is the weather in Philadelphia, PA?"
    print(f"Sending message: {req_msg}\n")
    msg = client.send_message(req_msg)
    print(f"Final message: {msg}\n")


if __name__ == "__main__":
    upload_and_link_functions()
    run_weather_chatbot()
```

## Developer / Contributing

While Iudex is currently in its nascent stages, we welcome contributions from the developer community.

We use Poetry for dependency management and packaging.

To get started:

1. Fork the repository and clone it locally.
2. Install Poetry on your system if you haven't already.
3. Run `poetry install` to install dependencies and the project as editable using `pip install --editable .`.
4. Run scripts or tests with `poetry run` or `poetry run pytest -s`. Alternatively start a nested shell with `poetry shell`.
