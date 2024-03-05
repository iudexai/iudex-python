from datetime import datetime, timezone
from typing import Any, Iterable, Union

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import Function as FunctionCall
from typing_extensions import Literal

from .resource import ApiResource


class IudexCompletions(ApiResource):
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
        # TODO: proper pydantic and TypedDict parsing
        messages: list[dict[str, Any]] = [dict(m) for m in messages]
        if not messages:
            raise ValueError("Must supply at least one message")

        last_msg_content = messages[-1].get("content")
        function_call_id = messages[-1].get("tool_call_id")

        # function_call_id provided, so we submit the function_return
        if function_call_id:
            res = self._client._request(
                "PUT",
                f"/function_calls/{function_call_id}/return",
                {"functionReturn": last_msg_content},
            )
        # no function_call_id provided, so we create a new workflow
        else:
            res = self._client._request(
                "POST",
                "/workflows",
                {"query": last_msg_content},
            )

        workflow_id = res.get("workflowId")
        if not workflow_id:
            raise ValueError("No workflow_id returned from Iudex")

        m = self._client._poll(
            "GET",
            f"/workflows/{workflow_id}/next_message",
        )

        # TODO: pydantic validation
        dt = datetime.fromisoformat(m["timestamp"].rstrip("Z")).replace(
            tzinfo=timezone.utc
        )
        timestamp = int(dt.timestamp())
        if m["type"] == "functionCall":
            message = ChatCompletionMessage(
                role="assistant",
                tool_calls=[
                    ChatCompletionMessageToolCall(
                        id=m["functionCallId"],
                        function=FunctionCall(
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


class IudexChat(ApiResource):
    @property
    def completions(self) -> IudexCompletions:
        return IudexCompletions(self._client)
