# https://pokeapi.co/docs/v2#pokemon-section
import httpx

from iudex import Iudex

get_pokemon_function_json = {
    "name": "get_pokemon",
    "description": "Get Pokémon data by id or name.",
    "parameters": {
        "type": "object",
        "properties": {
            "id_or_name": {
                "type": "string",
                "description": "The id or fully lowercase name of the Pokémon to get.",
            },
        },
    },
    "returns": {
        "description": "Object with Pokémon data such as name, base experience, and height.",
        "type": "object",
        "properties": {
            "id": {
                "description": "The identifier for this resource.",
                "type": "integer",
            },
            "name": {
                "description": "The name for this resource.",
                "type": "string",
            },
            "base_experience": {
                "description": "The base experience gained for defeating this Pokémon.",
                "type": "integer",
            },
            "height": {
                "description": "The height of this Pokémon in decimetres.",
                "type": "integer",
            },
            "weight": {
                "description": "The weight of this Pokémon in hectograms.",
                "type": "integer",
            },
            "stats": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "base_stat": {
                            "type": "integer",
                            "description": "The base value of the stat.",
                        },
                        "effort": {
                            "type": "integer",
                            "description": "The effort points (EVs) gained by defeating this Pokémon.",
                        },
                        "stat": {
                            "type": "object",
                            "description": "The stat the Pokémon has.",
                            "properties": {
                                "name": {
                                    "type": "string",
                                },
                                "url": {
                                    "type": "string",
                                },
                            },
                        },
                    },
                },
            },
            "types": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "slot": {
                            "type": "integer",
                            "description": "The order the Pokémon's types are listed in.",
                        },
                        "type": {
                            "type": "object",
                            "description": "The type the Pokémon has.",
                            "properties": {
                                "name": {
                                    "type": "string",
                                },
                                "url": {
                                    "type": "string",
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


def get_pokemon(id_or_name: str):
    res = httpx.get(f"https://pokeapi.co/api/v2/pokemon/{id_or_name}")
    res.raise_for_status()

    # cull the response to only the properties we want
    ret = {}
    for k, v in res.json().items():
        if k in get_pokemon_function_json["returns"]["properties"]:
            ret[k] = v
    return ret


##### Example usage #####
if __name__ == "__main__":
    iudex = Iudex()

    # Upload functions
    iudex.functions.upsert(functions=[get_pokemon_function_json])

    # Link functions
    iudex.link_functions({"get_pokemon": get_pokemon})

    # Send message (handles function calls)
    req_msg = "What is pikachu's height and weight?"
    print("Sending message:", req_msg)
    msg = iudex.send_message(req_msg)

    print("Final message:", msg)
