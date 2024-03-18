from datetime import datetime, timezone
from typing import Any, Iterable, Optional, Union

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionToolParam,
    completion_create_params,
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
        functions: Optional[Iterable[completion_create_params.Function]] = None,
        tools: Optional[Iterable[ChatCompletionToolParam]] = None,
        **kwargs,
    ) -> ChatCompletion:
        """Receives either a text or function call message from Iudex.

        If functions or tools are provided, the Iudex API will be called,
        receiving either a text or function call message.

        When a function call message is received, the requested function should be run
        and its result should be appended as a new message, following the OpenAI schema:
        ```
        {
            'tool_call_id': 'call_123456',
            'role': 'tool',
            'content': '{ "key": "value" }',
        }
        ```
        Finally, the `create` method should be called again with the new message.

        Receiving a non-function call (text) message indicates that the user query was resolved
        through function calling. The text content contains the final answer/response to the query.

        This method is compatible with `OpenAI.chat.completions.create`.
        If no functions or tools are provided, this method will directly call the OpenAI chat API.
        This requires an `OPENAI_API_KEY` environment variable to be set.

        Args:
            messages: A list of messages to send to Iudex.
                Currently, only the last message is used as the query.
                Support for context-sensitive function call planning is coming soon.
            model: The model to use for completion.
                This parameter is used for compatibility with the OpenAI API.
                For non-function calling chats, the model is passed along to the OpenAI API.
                Otherwise, it is unused; model switching support in Iudex is coming soon.
            functions: A list of function JSONs.
                This parameter is used for compatibility with the OpenAI API.
                If provided, the Iudex API is called to resolve the query with function calls.
                If neither functions nor tools are provided, the OpenAI API is called directly.
                The functions JSONs provided here are unused; instead Iudex uses functions JSONs
                uploaded via `iudex.Iudex.upsert_functions`.
            tools: A list of tool JSONs.
                This parameter is used for compatibility with the OpenAI API.
                If provided, the Iudex API is called to resolve the query with function calls.
                If neither functions nor tools are provided, the OpenAI API is called directly.
                The tool JSONs provided here are unused; instead Iudex uses functions JSONs uploaded
                via `iudex.Iudex.upsert_functions`.
            kwargs: Additional parameters to pass to the OpenAI API.

        Returns:
            ChatCompletion: The Open AI chat completion object.
                The Iudex client is compatible with OpenAI types and schemas; this returned object
                should be handled as normal.
        """
        # direct pass through to OpenAI API if not function calling
        if not functions and not tools:
            return self._client._openai_client.chat.completions.create(
                messages=messages, model=model, **kwargs
            )

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
