# initialize client
from iudex import Iudex

my_client = Iudex()  # set IUDEX_API_KEY env var or pass directly as arg

# write function JSONs
add_numbers_spec = {
    "name": "add_numbers",
    "description": "Adds two numbers together.",
    "parameters": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "The first number to add."},
            "b": {"type": "number", "description": "The second number to add."},
        },
        "required": ["a", "b"],
    },
    "returns": {"type": "number"},
}

subtract_numbers_spec = {
    "name": "subtract_numbers",
    "description": "Subtracts two numbers.",
    "parameters": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "The number to subtract from."},
            "b": {"type": "number", "description": "The number to subtract."},
        },
        "required": ["a", "b"],
    },
    "returns": {"type": "number"},
}

multiply_numbers_spec = {
    "name": "multiply_numbers",
    "description": "Multiplies two numbers.",
    "parameters": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "The first number to multiply."},
            "b": {"type": "number", "description": "The second number to multiply."},
        },
        "required": ["a", "b"],
    },
    "returns": {"type": "number"},
}

divide_numbers_spec = {
    "name": "divide_numbers",
    "description": "Divides two numbers.",
    "parameters": {
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
                "description": "The dividend, the number to divide.",
            },
            "b": {
                "type": "number",
                "description": "The divisor, the number by which to divide.",
            },
        },
        "required": ["a", "b"],
    },
    "returns": {"type": "number"},
}

# upload function JSONs
my_client.functions.upsert(
    functions=[
        add_numbers_spec,
        subtract_numbers_spec,
        multiply_numbers_spec,
        divide_numbers_spec,
    ]
)


# link function implementations
def add_numbers(a: int, b: int) -> int:
    return a + b


def subtract_numbers(a: int, b: int) -> int:
    return a - b


def multiply_numbers(a: int, b: int) -> int:
    return a * b


def divide_numbers(a: int, b: int) -> float:
    return a / b


my_client.link_functions(
    {
        "add_numbers": add_numbers,
        "subtract_numbers": subtract_numbers,
        "multiply_numbers": multiply_numbers,
        "divide_numbers": divide_numbers,
    }
)

# finally, ask iudex a question
query = """
Alice has 123 apples and 456 bananas.
Bob had 789 oranges but lost 420 of them.
What's the average number of fruits owned per person?
"""
response = my_client.send_message(query)
print(response)
assert "474" in response
