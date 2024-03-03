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
}


def get_current_weather(location: str, unit="fahrenheit"):
    print(f"Getting weather for {location} in {unit}...\n")
    temp = 70
    if unit == "celsius":
        temp = temp // 2
    return {
        "temp": temp,
        "unit": unit,
        "humidity": 0.5,
        "wind_speed": 1,
        "wind_unit": "mph",
        "wind_direction": "NE",
        "precipitation": 0.1,
        "description": "partially sunny",
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


def test_readme_example():
    print("running test_readme_example()\n")
    upload_and_link_functions()
    run_weather_chatbot()
