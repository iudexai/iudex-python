import datetime
import logging
import os
from typing import Union

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter
import openai

from iudex.fastapi import instrument_fastapi

load_dotenv()

api_key = os.getenv("IUDEX_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
router = APIRouter()
router2 = APIRouter()

if openai_api_key:
    openai.api_key = openai_api_key

@app.get("/")
def read_root():
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
    if openai.api_key:
        chat = openai.ChatCompletion.create(
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

iudex_config = instrument_fastapi(
    app=app,
    config={
        "service_name": __name__,
        "iudex_api_key": api_key,
        "env": "dev",
    }
)

app.include_router(router)

# should 404
@router.get('/health_2')
def health_2():
    return {'status': 'dokay'}

# should 404
@router2.get('/v2/health_2')
def v2_healt_2():
    return {'status': 'fffffffffffff'}

logger = logging.getLogger(__name__)

def post_fork(server, worker):
    instrument_fastapi(app)

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    res = {"item_id": item_id, "q": q}
    logger.info(res)
    return res

@app.post("/logs")
def logs(data):
    print(data)
    return {"data": data}
