import json
from iudex import Iudex
from openai.types.chat.completion_create_params import Function

client = Iudex()

get_current_weather_spec = Function(
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
)

def get_current_weather(location, unit='fahrenheit'):
    temp = 70
    if unit == 'celsius':
        temp = temp // 2
    return {
        'temp': temp,
        'unit': unit,
        'humidity': 0.5,
        'wind_speed': 1,
        'wind_unit': 'mph',
        'wind_direction': 'NE',
        'precipitation': 0.1,
        'description': 'partially sunny',
    }

NAME_TO_FUNCTION = {
    'get_current_weather': get_current_weather,
}

def upload_functions():
    functions = [get_current_weather_spec]
    client.functions.upsert(functions=functions, module='weather_module')
    print('Successfully uploaded functions!\n')

def run_weather_chatbot():
    messages = [{'role': 'user', 'content': 'What is the weather in Philadelphia, PA?'}]

    while True:
        res = client.chat.completions.create(
            messages=messages,
            model='gpt-4-turbo-preview',
        )

        msg = res.choices[0].message
        messages.append(msg)

        tool_calls = msg.tool_calls
        if not tool_calls:
            break

        print('message:', messages[-1], '\n')

        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            if fn_name not in NAME_TO_FUNCTION:
                raise ValueError(f'Unsupported function name: {fn_name}')
            fn = NAME_TO_FUNCTION[fn_name]

            fn_args = tool_call.function.arguments.replace('\'', '\"').replace('None', '\"null\"')
            print('fn_args:', fn_args, '\n')
            fn_return = fn(**json.loads(fn_args))
            print('fn_return:', json.dumps(fn_return), '\n')

            messages.append(
                {
                    'role': 'tool',
                    'content': json.dumps(fn_return),
                    'tool_call_id': tool_call.id,
                }
            )
    
    print('Final response:', messages[-1], '\n')

if __name__ == '__main__':
    upload_functions()
    run_weather_chatbot()

def test_readme_example():
    print('running test_readme_example()\n')
    upload_functions()
    run_weather_chatbot()
