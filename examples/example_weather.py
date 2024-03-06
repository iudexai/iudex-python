import httpx

from iudex import Iudex

get_location_metadata_function_json = {
    "name": "getLocationMetadata",
    "description": "Get metadata for a location by latitude and longitude.",
    "parameters": {
        "type": "object",
        "properties": {
            "lat": {
                "type": "number",
                "description": "The latitude of the location to get metadata for.",
            },
            "lon": {
                "type": "number",
                "description": "The longitude of the location to get metadata for.",
            },
        },
    },
    "returns": {
        "description": "Metadata object for the location with: the forecast office, gridId, gridX, gridY",
        "type": "object",
        "properties": {
            "cwa": {
                "description": "The forecast office that has the forecast for this point.",
                "type": "string",
            },
            "gridId": {
                "description": "The grid identifier.",
                "type": "string",
            },
            "gridX": {
                "description": "The grid x coordinate.",
                "type": "integer",
            },
            "gridY": {
                "description": "The grid y coordinate.",
                "type": "integer",
            },
        },
    },
}
def get_location_metadata(lat: float, lon: float):
    # coerce
    lat, lon = float(lat), float(lon)
    response = httpx.get(f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}", headers={"User-Agent": "example-weather"})
    response.raise_for_status()
    return response.json()


get_gridpoint_forecast_function_json = {
    "name": "getGridpointForecast",
    "description": "Get the forecast for a gridpoint.",
    "parameters": {
        "type": "object",
        "properties": {
            "gridId": {
                "type": "string",
                "description": "The grid identifier.",
            },
            "gridX": {
                "type": "integer",
                "description": "The grid x coordinate.",
            },
            "gridY": {
                "type": "integer",
                "description": "The grid y coordinate.",
            },
        },
    },
    "returns": {
        "description": "Forecast object for the gridpoint.",
        "type": "object",
        "properties": {
            "updated": {
                "description": "The time the forecast was updated.",
                "type": "string",
            },
            "periods": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "description": "The name of the period.",
                            "type": "string",
                        },
                        "startTime": {
                            "description": "The start time of the period.",
                            "type": "string",
                        },
                        "endTime": {
                            "description": "The end time of the period.",
                            "type": "string",
                        },
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
            },
        },
    },
}
def get_gridpoint_forecast(gridId: str, gridX: int, gridY: int):
    response = httpx.get(
        f"https://api.weather.gov/gridpoints/{gridId.upper()}/{gridX},{gridY}/forecast",
        headers={"User-Agent": "example-weather"},
    )
    response.raise_for_status()
    return response.json()

get_location_coordinate_function_json = {
    "name": "getLocationCoordinate",
    "description": "Get the latitude and longitude for a location string.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The location to get the latitude and longitude for in snake_case.",
            },
        },
    },
    "returns": {
        "description": "The latitude and longitude for the location.",
        "type": "object",
        "properties": {
            "latt": {
                "description": "The latitude of the location.",
                "type": "string",
            },
            "longt": {
                "description": "The longitude of the location.",
                "type": "string",
            },
        },
    },
}
def get_location_coordinate(location: str):
    response = httpx.get(f"https://geocode.xyz/{location}?json=1")
    response.raise_for_status()
    return response.json()

NAME_TO_FUNCTION = {
    "getLocationMetadata": get_location_metadata,
    "getGridpointForecast": get_gridpoint_forecast,
    "getLocationCoordinate": get_location_coordinate,
}


##### Example usage #####
if __name__ == "__main__":
    iudex = Iudex()

    # Upload functions
    iudex.functions.upsert(functions=[
        get_location_metadata_function_json,
        get_gridpoint_forecast_function_json,
        get_location_coordinate_function_json,
    ])

    # Link functions
    def function_linker(name: str):
        if name == "getLocationMetadata":
            return get_location_metadata
        if name == "getGridpointForecast":
            return get_gridpoint_forecast
        if name == "getLocationCoordinate":
            return get_location_coordinate
    iudex.link_functions(function_linker)

    # Send message (handles function calls)
    req_msg = "What's the weather in San Francisco?"
    print(f"Sending message: {req_msg}\n")
    msg = iudex.send_message(req_msg)

    print(f"Final message: {msg}\n")
