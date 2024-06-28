# Iudex

Next generation observability.

### Table of contents
- [Iudex](#iudex)
    - [Table of contents](#table-of-contents)
- [Getting Started](#getting-started)
    - [Autoinstrument](#autoinstrument)
    - [Modal](#modal)
    - [Tracing Your Functions](#tracing-your-functions)
- [Slack Alerts](#slack-alerts)


# Getting Started
Instrumenting your Python code with Iudex just takes a few steps.

1. Install dependencies.
```bash
pip install iudex
```
2. Follow the below instructions for your frameworks or use autoinstrumentation.
3. Make sure your app has access to the environment variable `IUDEX_API_KEY`. You can manually add this to `instrument` as well if you use something like a secrets manager.
4. You should be all set! Go to [https://app.iudex.ai/](https://app.iudex.ai/) and enter your API key.
5. Go to [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and press `Search` to view your logs.

### Autoinstrument
[Supported libraries from OTel](https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/README.md):

✅ aio-pika
✅ aiohttp-client
✅ aiohttp-server
✅ aiopg
✅ asgi
✅ asyncio
✅ asyncpg
✅ aws-lambda
✅ boto
✅ boto3sqs
✅ botocore
✅ cassandra
✅ celery
✅ confluent-kafka
✅ dbapi
✅ django
✅ elasticsearch
✅ falcon
✅ fastapi
✅ flask
✅ grpc
✅ httpx
✅ jinja2
✅ kafka-python
✅ logging
✅ mysql
✅ mysqlclient
✅ pika
✅ psycopg
✅ psycopg2
✅ pymemcache
✅ pymongo
✅ pymysql
✅ pyramid
✅ redis
✅ remoulade
✅ requests
✅ sklearn
✅ sqlalchemy
✅ sqlite3
✅ starlette
✅ system-metrics
✅ threading
✅ tornado
✅ tortoiseorm
✅ urllib
✅ urllib3
✅ wsgi

[Supported libaries from OpenLLMetry](https://github.com/traceloop/openllmetry?tab=readme-ov-file#-what-do-we-instrument):

✅ OpenAI / Azure OpenAI
✅ Anthropic
✅ Cohere
✅ Ollama
✅ Mistral AI
✅ HuggingFace
✅ Bedrock (AWS)
✅ Replicate
✅ Vertex AI (GCP)
✅ Google Generative AI (Gemini)
✅ IBM Watsonx AI
✅ Together AI
✅ Aleph Alpha
✅ Chroma
✅ Pinecone
✅ Qdrant
✅ Weaviate
✅ Milvus
✅ Marqo
✅ LangChain
✅ LlamaIndex
✅ Haystack
✅ LiteLLM

Supported libraries:

✅ logger
✅ sqlalchemy
✅ supabase


Add this code the top of your entrypoint file (usually `main.py`).
```python
from iudex.instrumentation import instrument
instrument(
  service_name=<your_service_name>, # highly encouraged
  env=<your_environment>, # optional
)
```
You should be all set! Iudex will now record logs and trace the entire life cycle for each request.

Go to [https://app.iudex.ai/](https://app.iudex.ai/) to start viewing your logs and traces!

For libraries that are not autoinstrumented or custom deployment environments, follow the instructions from the table of contents for that specific library.


### Modal
Because Modal only loads libraries after running a particular serverless function, you need follow [their suggestions for using packages](https://modal.com/docs/guide/custom-container#add-python-packages-with-pip_install).

For example:
```python
@app.function(image=image, secrets=[modal.Secret.from_name("iudex-api-key")])
def square(x):
    import logging
    from iudex import instrument

    instrument(service_name="test-modal-instrumentation", env="development")

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("This log shows up on Iudex!")
    return x**2
```

### Tracing Your Functions
We recommend tracing important functions in your codebase, i.e. when it would be helpful to see in a stack trace.

Note: You must call `iudex.instrument()` earlier in your code before the traced function is invoked.

```python
from iudex import instrument, trace

@trace()
def my_function(arg1, arg2):
  pass
```

# Slack Alerts
You can easily configure Slack alerts on a per-log basis.

First visit [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and click on the `Add to Slack` button in the top right.

Once installed to your workspace, tag your logs with the `iudex.slack_channel_id` attribute.
```python
logger.info("Hello from Slack!", extra={"iudex.slack_channel_id": "YOUR_SLACK_CHANNEL_ID"})
```
Your channel ID can be found by clicking the name of the channel in the top left, then at the bottom of the dialog that pops up.

As long as the channel is public or you've invited the Iudex app, logs will be sent as messages to their tagged channel any time they are logged.
