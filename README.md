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

Before running the examples below, make sure to set the `IUDEX_API_KEY` environment variable or pass your API key directly to the `Iudex` constructor.

Visit [iudex.ai](https://iudex.ai) to sign up and receive an API key.

```python
from iudex import Iudex
from openai.types.chat.completion_create_params import Function

client = Iudex(
    api_key='YOUR_API_KEY', # alternatively, set the `IUDEX_API_KEY` environment variable
)

def upload_functions():
    functions = [
        Function(
            name='get_current_weather',
            description='Gets the current weather',
            parameters={
                'type': 'object',
                'properties': {
                    'location': {
                        'type': 'string',
                        'description': 'The city and state, e.g., San Francisco, CA',
                    },
                    'unit': {
                        'type': 'string',
                        'enum': ['celsius', 'fahrenheit'],
                        'description': 'The temperature unit',
                    },
                },
                'required': ['location'],
            },
        ),
    ]

    res = client.functions.upsert(functions=functions, module='weather_module')
    print('Successfully uploaded functions!')

def check_weather():
    messages = [{'role': 'user', 'content': 'What is the weather in Philadelphia, PA?'}]

    while True:
        print(messages[-1], '\n\n')

        res = client.chat.completions.create(
            messages=messages,
            model='gpt-3.5-turbo',
        )

        msg = res.choices[0].message
        messages.append(msg)

        tool_calls = msg.get('tool_calls', [])
        if not tool_calls:
            break

        for tool_call in tool_calls:
            fn_call_id = tool_call['id']
            fn_name = tool_call['function']['name']
            fn_args = tool_call['function']['arguments']

            fn_return = get_current_weather(fn_name, fn_args)

            messages.append(
                {'role': 'tool', 'content': fn_return, 'tool_call_id': fn_call_id}
            )

def get_current_weather(fn_name, fn_args):
    return "It's always sunny"

if __name__ == '__main__':
    upload_functions()
    check_weather()
```

## Developer / Contributing

While Iudex is currently in its nascent stages, we welcome contributions from the developer community.

We use Poetry for dependency management and packaging.

To get started:

1. Fork the repository and clone it locally.
2. Install Poetry on your system if you haven't already.
3. Run `poetry install` to install dependencies and the project as editable.
4. Run scripts or tests with `poetry run` or start a nested shell with `poetry shell`.
