from __future__ import annotations

from datetime import datetime, timezone
import os
import time
from typing import (
    Any,
    Dict,
    Iterable,
    Optional,
    Union,
)
from typing_extensions import Literal

import httpx
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import Function

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
)


class IudexCompletions:
    _client: Iudex

    def __init__(self, client: Iudex) -> None:
        self._client = client

    def create(
        self,
        *,
        messages: Iterable[ChatCompletionMessageParam],
        # TODO: warn following args are not currently used
        model: Union[
            str,
            Literal[
                "gpt-4-0125-preview",
                "gpt-4-turbo-preview",
                "gpt-4-1106-preview",
                "gpt-4-vision-preview",
                "gpt-4",
                "gpt-4-0314",
                "gpt-4-0613",
                "gpt-4-32k",
                "gpt-4-32k-0314",
                "gpt-4-32k-0613",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-3.5-turbo-0301",
                "gpt-3.5-turbo-0613",
                "gpt-3.5-turbo-1106",
                "gpt-3.5-turbo-0125",
                "gpt-3.5-turbo-16k-0613",
            ],
        ],
        **kwargs,
    ) -> ChatCompletion:
        messages = list(messages)
        if not messages:
            raise ValueError("Must supply at least one message")

        last_msg_content = messages[-1].get("content")
        function_call_id = messages[-1].get("tool_call_id")

        # function_call_id provided, so we submit the function_return
        if function_call_id:
            res = self._client.request(
                "PUT",
                f"/function_calls/{function_call_id}/return",
                {"functionReturn": last_msg_content},
            )
        # no function_call_id provided, so we create a new workflow
        else:
            res = self._client.request(
                "POST",
                "/workflows",
                {"query": last_msg_content},
            )

        workflow_id = res.get("workflowId")
        if not workflow_id:
            raise ValueError("No workflow_id returned from Iudex")

        m = self._client.poll(
            "GET",
            f"/workflows/{workflow_id}/next_message",
        )

        # TODO: pydantic validation
        dt = datetime.fromisoformat(m["timestamp"].rstrip("Z")).replace(tzinfo=timezone.utc)
        timestamp = int(dt.timestamp())
        if m["type"] == "functionCall":
            message = ChatCompletionMessage(
                role="assistant",
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        id=m["functionCallId"],
                        function=Function(
                            arguments=str(m["functionArgs"]), name=m["functionName"]
                        ),
                        type="function",
                    )
                ],
            )
            return ChatCompletion(
                id=m["id"],
                choices=[Choice(finish_reason="tool_calls", index=0, message=message)],
                model=model,
                object="chat.completion",
                created=timestamp,
            )

        if m["type"] == "text":
            message = ChatCompletionMessage(
                content=m["text"],
                role="assistant",
            )
            return ChatCompletion(
                id=m["id"],
                choices=[Choice(finish_reason="stop", index=0, message=message)],
                model=model,
                object="chat.completion",
                created=timestamp,
            )

        raise ValueError(f"Unsupported message type: {m['type']}")


class IudexChat:
    _client: Iudex

    def __init__(self, client: Iudex) -> None:
        self._client = client

    @property
    def completions(self) -> IudexCompletions:
        return IudexCompletions(self._client)


class Iudex:
    base_url = "https://api.iudex.ai"
    api_key: str
    chat: IudexChat

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.getenv("IUDEX_API_KEY")
        if not api_key:
            raise ValueError(
                'Must supply an API key by setting env var IUDEX_API_KEY or as arg (`Iudex(api_key="YOUR_API_KEY")`)'
            )
        self.api_key = api_key
        self.base_url = base_url or os.getenv("IUDEX_BASE_URL") or self.base_url
        self.chat = IudexChat(self)

    def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        return self._request(method, path, data, params).json()

    def poll(
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
            response = self._request(method, path, data, params)
            if response.status_code == 204:
                tries += 1
                time.sleep(wait_seconds)
                continue
            return response.json()
        raise TimeoutError("Max retries reached without a successful response.")

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 30,
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
