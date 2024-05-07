# Iudex Python Client

**✨ Build 🛠 With Next Gen LLM Function Calling ✨**

[Iudex](https://iudex.ai) is an agent accessible via API that provides more accurate, secure, and scalable LLM function calling.
- Scales to support 1000s of functions per query, not 10s
- Supports arbitrarily complex queries and automatically handles edgecases
- Ensures accuracy and interpretability using automated task orchestration
- Iudex never has to ingest your code or data

Sign Up at [iudex.ai](https://iudex.ai) or shoot a message at support@iudex.ai to get an API key.

## Installation

```bash
pip install iudex
```

## How Iudex Works

![Iudex flow diagram](https://gist.github.com/assets/2763712/be399690-bc8b-4f52-9e1f-228a3d2d6c4e)

## Quickstart
<details>
<summary>Code Snippet</summary>
Before running, make sure to set the `IUDEX_API_KEY` environment variable or pass your API key directly to the `Iudex` constructor.

Visit [iudex.ai](https://iudex.ai) to sign up and receive an API key.

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

More [`examples`](https://github.com/iudexai/iudex-python/tree/main/examples)
</details>

## How It Works

### tl;dr - Two steps
1. Upload ALL your function JSONs
2. Run your most complex queries in natural language

### 0. Initialize Iudex client
You'll first need a Iudex API key, which you can obtain by signing up at [iudex.ai](https://iudex.ai).

Then set the environment variable:
```bash
export IUDEX_API_KEY='ixk_asdf1234'
```

And initialize the client in your code:
```python
from iudex import Iudex

my_client = Iudex()
```

### 1. Write function JSONs
Function JSONs describe your functions and their parameter/return schemas using [JSON schema](https://json-schema.org).

Functions will be used to resolve queries.
Iudex never sees your code - the functions run on your server, and you only need to upload the returned results.
This way, everything stays secure in your environment; you never have to share credentials or open ports.

Example function JSON for a function `get_current_weather(location: str, unit: str): dict`:
```json
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
```
Use `iudex.types.function.FunctionJson` to help structure and validate your function JSONs.
If you've written function JSONs for OpenAI function calling, you can convert them with `FunctionJson.from_openai_function`.

### 2. Upload function JSONs
Upload your function JSONs with
```python
my_client.functions.upsert([get_current_weather_spec])
```
For each query, Iudex will intelligently select and plan the execution of relevant functions, regardless of how many functions are uploaded.

❗Yes, you can upload as many functions as you want!

We've found that having a greater number of atomic functions outperforms having fewer monolithic functions.
However, function calling LLMs force you to reduce the number of functions per query because of the context window.
Iudex can scale up to as many functions as you need,
so try breaking up your "omni functions" to see how much your system's accuracy improves!

### 3. [Optional] Link functions
Link function implementations to their JSON specs by name.
```python
def get_current_weather(...):
    ...

my_client.link_functions({
    "get_current_weather": get_current_weather
})
```
This helps the Iudex client invoke functions in your runtime on your behalf.
Otherwise, you'd have to write a lot of boilerplate to handle intermediate function calls from Iudex.

You can pass in a simple dictionary or a function such as:
```python
def linker(fn_name: str):
    print(f"Getting function '{fn_name}'")
    if name == "get_current_weather":
        update_metrics(fn_name)
        return get_current_weather
```
Using a function over a dict can be useful when you want side effects like logging or analytics,
since the Iudex client will otherwise abstract away this intermediate logic.

### 4. Run query
Send a complex natural language query to Iudex:
```python
response = my_client.send_message("What's the weather in Philadelphia, PA?")
print("Bot:", response)
```
Iudex uses multi-agent orchestration to resolve queries.
Broadly, it selects the right functions, identifies the right sequence of function calls with any necessary transformations, and runs each step of the sequence.

Iudex is self-healing.
When encountering errors or too-complex queries, it simplifies the query to smaller subtasks, then selecting the right functions, etc. for each subtask.

Iudex workflows are auditable.
Visit the [dashboard](https://app.iudex.ai) to monitor Iudex's progress on your queries at a highly granular level.

## OpenAI Compatibility
The Iudex python client is compatible with the OpenAI python client's chat completions API.
If you already use function calling with OpenAI, you can integrate Iudex with two lines of code.
```diff
from openai import OpenAI
+ from iudex import Iudex

- client = OpenAI()
+ client = Iudex()
```
Compatibility with the OpenAI Assistants API is coming soon.

## For Developers / Contributing

While Iudex is currently in its nascent stages, we welcome contributions from the developer community.

We use [Poetry](https://python-poetry.org) for dependency management and packaging.

To get started:

1. [Fork the repository](https://github.com/iudexai/iudex-python/fork) and clone it locally.
2. [Install Poetry](https://python-poetry.org/docs/#installation) on your system if you haven't already.
3. Run `poetry install` to install dependencies and the project as editable.
4. Run scripts or tests with `poetry run` or `poetry run pytest -s`. Alternatively start a nested shell and load the venv with `poetry shell`.
5. Run `python3 -m venv venv` and `source venv/bin/activate` to set up the environment.
