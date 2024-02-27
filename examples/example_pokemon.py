# https://pokeapi.co/docs/v2#pokemon-section
import json

import httpx

from iudex import Iudex

get_pokemon_function_json = {
    "name": "getPokemon",
    "description": "Get Pokémon data by id or name.",
    "parameters": {
        "type": "object",
        "properties": {
            "idOrName": {
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


NAME_TO_FUNCTION = {"getPokemon": get_pokemon}


##### Example usage #####
if __name__ == "__main__":
    # Load client - remember to set the IUDEX_API_KEY env var or pass in here
    iudex = Iudex()

    # Upload functions
    iudex.functions.upsert(functions=[get_pokemon_function_json])

    # Send message and handle function calls
    messages = [{"role": "user", "content": "What is pikachu's height and weight?"}]

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

            fn_args = tool_call.function.arguments.replace("'", '"').replace("None", '"null"')
            fn_return = fn(**json.loads(fn_args))

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(fn_return),
                    "tool_call_id": tool_call.id,
                }
            )
