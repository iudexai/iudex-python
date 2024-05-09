from dotenv import load_dotenv
load_dotenv()
import os

from typing import Union
from fastapi import FastAPI
import logging
from iudex.instrumentation.fastapi_instrumentation import instrument_app

api_key = os.getenv("IUDEX_API_KEY")
app = FastAPI()
instrument_app(app=app, api_key=api_key)

logger = logging.getLogger(__name__)

def post_fork(server, worker):
    instrument_app(app)

@app.get("/")
def read_root():
    logger.info("Hello World")
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    res = {"item_id": item_id, "q": q}
    logger.info(res)
    return res

@app.post("/logs")
def logs(data):
    print(data)
    return {"data": data}