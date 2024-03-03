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


##### Example usage #####
if __name__ == "__main__":
    iudex = Iudex()

    # Upload functions
    iudex.functions.upsert(functions=[search_yelp_function_json])

    # Link functions
    iudex.link_functions({"searchYelp": search_yelp})

    # Send message (handles function calls)
    req_msg = "Find me an upscale French restaurant in SF"
    print(f"Sending message: {req_msg}\n")
    msg = iudex.send_message(req_msg)

    print(f"Final message: {msg}\n")
