import logging
import os
from typing import Union

from dotenv import load_dotenv
from fastapi import FastAPI

from iudex.instrumentation.fastapi import instrument

load_dotenv()

api_key = os.getenv("IUDEX_API_KEY")
app = FastAPI()
instrument(app=app, service_name=__name__)

logger = logging.getLogger(__name__)


def post_fork(server, worker):
    instrument(app)


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
