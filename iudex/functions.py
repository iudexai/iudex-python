from typing import Any, Dict, Iterable, List, Optional, Union

from pydantic import ValidationError

from iudex.types.function import FunctionJson

from .resource import ApiResource


class IudexFunctions(ApiResource):
    def upsert(
        self,
        *,
        functions: Iterable[Union[FunctionJson, Dict[str, Any]]],
        module: Optional[str] = None,
    ):
        """Upserts functions JSONs to the Iudex API.

        Iudex will intelligently select and plan the execution of relevant
        functions per query, regardless of how many functions are uploaded.
        All uploaded functions are available to Iudex to resolve queries.

        Construct function JSONs using `iudex.types.function.FunctionJson`.
        It also has a utility method to convert from OpenAI function JSONs.

        Args:
            functions: The function JSONs to upsert.
                A list of `FunctionJson` objects or properly formatted dictionaries.
                Existing function JSONs of the same name will be updated.
            module: The name of the module under which to upload the function JSONs.
        """
        jsons: List[FunctionJson] = []
        for fn in functions:
            try:
                if not isinstance(fn, FunctionJson):
                    fn = FunctionJson(**fn)
                jsons.append(fn)
            except ValidationError as e:
                raise ValueError(f"Invalid function JSON structure: {e}")

        req: dict[str, object] = {"jsons": [fn.dict() for fn in jsons]}
        if module:
            req["module"] = module

        return self._client._request("PUT", "/function_jsons", req)
