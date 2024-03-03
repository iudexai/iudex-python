from typing import Any, Dict, Iterable, Optional

from openai.types.chat.completion_create_params import Function as FunctionSpec

from .resource import ApiResource


class IudexFunctions(ApiResource):
    def upsert(
        self,
        *,
        functions: Iterable[FunctionSpec],
        module: Optional[str] = None,
    ):
        req: Dict[str, Any] = {"jsons": functions}
        if module:
            req["module"] = module
        return self._client._request("PUT", "/function_jsons", req)
