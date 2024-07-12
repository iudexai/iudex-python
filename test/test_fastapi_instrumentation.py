from iudex import instrument

iudex_config = instrument()

import datetime
import logging
import os
from typing import Union
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from iudex import traced_fn
from openai import OpenAI

load_dotenv()

api_key = os.getenv("IUDEX_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

app = FastAPI()
router = APIRouter()
router2 = APIRouter()

oai_client = None
if openai_api_key:
    oai_client = OpenAI(api_key=openai_api_key)

supabase = None
if supabase_url and supabase_key:
    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)

logger = logging.getLogger(__name__)

@app.get("/")
def read_root():
    logger.info("Hello world")
    return {"data": "hello world"}

@app.get("/print_error")
def print_error():
    e = ValueError("This is an error")
    logger.exception(e)
    return {"data": "hello world"}

@app.get("/supabase")
def test_supabase():
    if not oai_client or not supabase:
        raise ValueError("Please set OPENAI_API_KEY and SUPABASE_URL/SUPABASE_KEY")
    logger.info("Starting test_supabase_instrumentation")
    logger.info("Creating chat")
    res = oai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "tell me a joke involving supabase and opentelemetry!",
            }
        ],
    )
    content = res.choices[0].message.content
    logger.info("No op Fetching 0 chats")
    res = supabase.table("chat").select("id, content, thread(id)").eq("id", uuid4()).execute()
    logger.info(f"Storing LLM response: {content}")
    supabase.table("chat").upsert({"id": str(uuid4()), "content": content}).execute()
    logger.info("Fetching chat")
    res = supabase.table("chat").select("*").execute()
    logger.info("Finished test_supabase_instrumentation")
    return {"data": res}

@app.get("/openai")
def test_openai():
    recursive: dict = {"primitive": "value"}
    recursive["recursive"] = recursive
    error = ValueError("This is an error")
    msg = f"Log from {datetime.datetime.now()}"
    logger.info(
        msg,
        extra={
            "my_attribute_1": "primitive value",
            "my_attribute_2": {"nested": {"name": "value"}},
            "my_attribute_3": recursive,
            "my_error": error,
            "iudex.slack_channel_id": "YOUR_SLACK_CHANNEL_ID",
        },
    )

    # LLM call should be logged and traced automatically
    chat = None
    if oai_client:
        chat = oai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Your name is Bob."},
                {"role": "user", "content": "Hi what's your name?"}
            ]
        )

    return {"data": msg, "chat": chat}

@router.get('/health')
def health():
    return {'status': 'ok'}

@router2.get('/v2/health')
def v2_health():
    return {'status': 'okok'}

app.include_router(router2)

app.include_router(router)

# should 404
@router.get('/health_2')
def health_2():
    return {'status': 'dokay'}

# should 404
@router2.get('/v2/health_2')
def v2_healt_2():
    return {'status': 'fffffffffffff'}

print('GIT_COMMIT:', iudex_config.git_commit)
print('GITHUB_URL:', iudex_config.github_url)
print('API_KEY:', iudex_config.iudex_api_key)

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    res = {"item_id": item_id, "q": q}
    logger.info(res)
    return res


@app.post("/logs")
def logs(data):
    print(data)
    return {"data": data}

@app.get("/neutrino")
def neutrino():
    neutrino_api_key = os.getenv("NEUTRINO_API_KEY")
    nclient = OpenAI(
        base_url="https://router.neutrinoapp.com/api/engines",
        api_key=neutrino_api_key,
    )
    logger.info("Starting neutrino test")
    logger.info("Creating chat")
    def stream_res():
        for chunk in nclient.chat.completions.create(
            model="chat-preview",
            messages=[
                {
                    "role": "user",
                    "content": "Tell me a funny joke.",
                }
            ],
            stream=True,
        ):
            yield chunk.choices[0].delta.content or ""
    return StreamingResponse(stream_res())

if __name__ == "__main__":
    traced_fn()
