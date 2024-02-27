import json
import os

import httpx

from iudex import Iudex

# Define the searchYelp function JSON
search_yelp_function_json = {
    "name": "searchYelp",
    "description": "Search Yelp for businesses.",
    "parameters": {
        "type": "object",
        "properties": {
            "term": {
                "type": "string",
                "description": "The search term, for example 'food' or 'restaurant name'.",
            },
            "location": {
                "type": "string",
                "description": "The search location, for example 'san francisco'.",
            },
        },
    },
    "returns": {
        "description": "Array of businesses and attributes: name, url, categories, and hours.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the business.",
                },
                "url": {
                    "type": "string",
                    "description": "The url of the business.",
                },
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "alias": {
                                "type": "string",
                                "description": "The alias of the category.",
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the category.",
                            },
                        },
                    },
                },
                "hours": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "hours_type": {
                                "type": "string",
                                "description": "The type of hours.",
                            },
                            "is_open_now": {
                                "type": "boolean",
                                "description": "Whether the business is open now.",
                            },
                            "open": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "day": {
                                            "type": "number",
                                            "description": "The day of the week.",
                                        },
                                        "end": {
                                            "type": "string",
                                            "description": "The end time of the business.",
                                        },
                                        "is_overnight": {
                                            "type": "boolean",
                                            "description": "Whether the business is open overnight.",
                                        },
                                        "start": {
                                            "type": "string",
                                            "description": "The start time of the business.",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


def search_yelp(term: str, location: str):
    yelp_api_key = os.getenv("YELP_API_KEY")
    if not yelp_api_key:
        raise ValueError("YELP_API_KEY environment variable is missing or empty.")
    url_params = {
        "term": term,
        "location": location,
        "limit": 20,
        "sort_by": "best_match",
    }
    headers = {
        "Authorization": f"Bearer {yelp_api_key}",
        "Accept": "application/json",
    }
    response = httpx.get(
        "https://api.yelp.com/v3/businesses/search",
        params=url_params,
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


NAME_TO_FUNCTION = {"searchYelp": search_yelp}


##### Example usage #####
if __name__ == "__main__":
    # Load client - remember to set the IUDEX_API_KEY env var or pass in here
    iudex = Iudex()

    # Upload functions
    iudex.functions.upsert(functions=[search_yelp_function_json])

    # Send message and handle function calls
    messages = [{"role": "user", "content": "Find me an upscale French restaurant in SF"}]

    while True:
        print(messages[-1], "\n\n")

        res = iudex.chat.completions.create(
            messages=messages,
            model="gpt-4-turbo-preview",
        )

        msg = res.choices[0].message
        messages.append(msg)

        tool_calls = msg.tool_calls
        if not tool_calls:
            break

        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            if fn_name not in NAME_TO_FUNCTION:
                raise ValueError(f"Unsupported function name: {fn_name}")
            fn = NAME_TO_FUNCTION[fn_name]

            fn_args = tool_call.function.arguments.replace("'", '"').replace(
                "None", '"null"'
            )
            fn_return = fn(**json.loads(fn_args))

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(fn_return),
                    "tool_call_id": tool_call.id,
                }
            )
