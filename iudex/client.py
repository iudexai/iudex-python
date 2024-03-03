from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, Optional, Union

import httpx

from .chat import IudexChat
from .functions import IudexFunctions
from .utils import clean_json


default_base_url = "https://api.iudex.ai"


class Iudex:
    base_url = os.getenv("IUDEX_BASE_URL") or default_base_url
    api_key: str
    chat: IudexChat
    functions: IudexFunctions

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.getenv("IUDEX_API_KEY")
        if not api_key:
            raise ValueError(
                'Must supply an API key by setting env var `IUDEX_API_KEY` or as arg (`Iudex(api_key="YOUR_API_KEY")`)'
            )
        self.api_key = api_key

        self.base_url = base_url or os.getenv("IUDEX_BASE_URL") or self.base_url

        self.chat = IudexChat(self)
        self.functions = IudexFunctions(self)

    def link_functions(
        self,
        function_linker: Union[
            Callable[[str], Optional[Callable[..., Any]]], Dict[str, Callable[..., Any]]
        ],
    ) -> None:
        """Links function names to their implementations.

        Args:
            function_linker (Union[Callable[[str], Callable[..., Any]], Dict[str, Callable[..., Any]]]):
                The mechanism for linking function names to their implementations. Can be either
                a callable that resolves function names to implementations (alongside potential side effects)
                or a simple dictionary mapping names to functions.
        """
        if callable(function_linker):
            self._function_linker = function_linker
        elif isinstance(function_linker, dict):
            self._function_linker = lambda fn_name: function_linker.get(fn_name)
        else:
            raise TypeError(
                "function_linker must be either a callable or a dictionary."
            )

    def get_function(self, function_name: str) -> Callable[..., Any]:
        """Retrieves a function implementation by name using the function linker.

        Args:
            function_name (str): The name of the function to retrieve.

        Returns:
            Callable[..., Any]: The function implementation associated with `function_name`.
        """
        if not hasattr(self, "_function_linker"):
            raise ValueError(
                "Function linker has not been set; use `link_functions` first"
            )
        function = self._function_linker(function_name)
        if function is None:
            raise ValueError(f"Unsupported function name: '{function_name}'")
        return function

    def send_message(
        self,
        message: str,
        model: str = "gpt-4-turbo-preview",
    ) -> str:
        messages = [{"role": "user", "content": message}]

        # loop until no more tool calls
        while True:
            # get next message
            res = self.chat.completions.create(
                messages=messages,
                model=model,
            )
            next_msg = res.choices[0].message
            messages.append(next_msg)

            tool_calls = next_msg.tool_calls

            # no more tool calls, so return text content
            if not tool_calls:
                if not next_msg.content:
                    raise ValueError("No content in OpenAI assistant message")
                return next_msg.content

            # otherwise resolve tool calls
            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn = self.get_function(fn_name)

                fn_args = clean_json(tool_call.function.arguments)
                fn_return = fn(**json.loads(fn_args))

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(fn_return, indent=2),
                        "tool_call_id": tool_call.id,
                    }
                )

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        return self._request_helper(method, path, data, params).json()

    def _poll(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        max_tries: int = 300,
        wait_seconds: int = 1,
    ) -> Dict[str, Any]:
        """Polls endpoint until it returns non-204 response."""
        tries = 0
        while tries < max_tries:
            response = self._request_helper(method, path, data, params)
            if response.status_code == 204:
                tries += 1
                time.sleep(wait_seconds)
                continue
            return response.json()
        raise TimeoutError("Max retries reached without a successful response.")

    def _request_helper(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 120,
    ):
        """Helper to make requests and return raw API response."""
        with httpx.Client(timeout=timeout_seconds) as client:
            headers = {"x-api-key": self.api_key}
            response = client.request(
                method=method,
                url=self.base_url + path,
                json=data,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            return response
