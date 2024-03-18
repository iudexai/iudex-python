from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)

from openai.types.chat.completion_create_params import Function as OpenAiFunction
from pydantic import BaseModel, root_validator, validator


class BaseJsonSchema(BaseModel):
    description: Optional[str]

    @root_validator(pre=False, skip_on_failure=True)
    def remove_none_values(cls, values):
        for key, value in list(values.items()):
            if value is None:
                del values[key]
        return values


class StringJsonSchema(BaseJsonSchema):
    type: Literal["string"] = "string"
    enum: Optional[List[str]]


class NumberJsonSchema(BaseJsonSchema):
    type: Literal["number", "integer"]
    minimum: Optional[float]
    maximum: Optional[float]


class BooleanJsonSchema(BaseJsonSchema):
    type: Literal["boolean"] = "boolean"


class NullJsonSchema(BaseJsonSchema):
    type: Literal["null"] = "null"


class UnknownJsonSchema(BaseJsonSchema):
    type: Literal["unknown"] = "unknown"


class ObjectJsonSchema(BaseJsonSchema):
    type: Literal["object"] = "object"
    properties: Dict[str, ValueJsonSchema]
    required: Optional[List[str]]

    @validator("properties", pre=True)
    def coerce_properties(cls, v):
        if isinstance(v, dict):
            for key, value in v.items():
                if "type" not in value:
                    v[key] = {"type": "unknown"}
        return v


class ArrayJsonSchema(BaseJsonSchema):
    type: Literal["array"] = "array"
    items: ValueJsonSchema


class TupleJsonSchema(BaseJsonSchema):
    type: Literal["array"] = "array"
    items: List[ValueJsonSchema]


# Invalid JSON Schema, but easier to understand
class UnionJsonSchema(BaseJsonSchema):
    type: List[str]


# Valid JSON Schema, harder to use
class RealUnionJsonSchema(BaseJsonSchema):
    anyOf: List[ValueJsonSchema]


ValueJsonSchema = Union[
    StringJsonSchema,
    NumberJsonSchema,
    BooleanJsonSchema,
    NullJsonSchema,
    UnknownJsonSchema,
    ObjectJsonSchema,
    ArrayJsonSchema,
    TupleJsonSchema,
    UnionJsonSchema,
    RealUnionJsonSchema,
]

# Update forward references for recursive types
for schema in [
    ObjectJsonSchema,
    ArrayJsonSchema,
    TupleJsonSchema,
    RealUnionJsonSchema,
]:
    schema.update_forward_refs()


class FunctionJson(BaseModel):
    """JSON schema to describe functions and their parameters and return schemas."""
    name: str
    description: Optional[str]
    parameters: Union[ObjectJsonSchema, ArrayJsonSchema]
    returns: ValueJsonSchema
    usageExample: Optional[str]
    returnsExample: Optional[str]

    @root_validator(pre=False, skip_on_failure=True)
    def remove_none_values(cls, values):
        for key, value in list(values.items()):
            if value is None:
                del values[key]
        return values

    @classmethod
    def from_openai_function(
        cls,
        function: OpenAiFunction,
        returns: Union[ValueJsonSchema, Dict[str, Any]],
        usageExample: Optional[str] = None,
        returnsExample: Optional[str] = None,
    ) -> "FunctionJson":
        """Convert an OpenAI Function to a Iudex FunctionJson.

        You must additionally supply a `returns` schema.

        Args:
            function (Function):
                The OpenAI Function TypedDict to convert.
            returns (Union[ValueJsonSchema, Dict[str, Any]]):
                The schema of the return value of the function, described as a JSON Schema object.
            usageExample (Optional[str]):
                An example of how to use the function. Defaults to None.
            returnsExample (Optional[str]):
                An example of a real return value. Defaults to None.
        """
        function_data = {
            "name": function["name"],
            "returns": returns,
        }

        description = function.get("description")
        if description:
            function_data["description"] = description

        parameters = function.get("parameters")
        if parameters:
            function_data["parameters"] = parameters

        if usageExample:
            function_data["usageExample"] = usageExample

        if returnsExample:
            function_data["returnsExample"] = returnsExample

        return cls(**function_data)
