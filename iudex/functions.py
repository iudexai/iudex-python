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
