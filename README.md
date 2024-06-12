# Iudex

Next generation observability.

# Getting Started

Instrumenting your Python service to send logs to Iudex just takes a few steps.

1. Pip install dependencies
```bash
pip install iudex
```
2. Import `instrument` from `iudex` and invoke it in your entrypoint (usually `main.py`)
```python
# Add this in your lambda function file (likely lambda_function.py)
from iudex.instrumentation import instrument
instrument(
  service_name=__name__, # or any string describing your service
  env="development", # or any string for your env
)
```
3. Make sure the app has access to the environment variable `IUDEX_API_KEY`
4. You should be all set! Go to [https://app.iudex.ai/](https://app.iudex.ai/) and enter your API key
5. Go to [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and press `Search` to view your logs


### FastAPI

If you use FastAPI, we highly recommend instrumenting your app for even more detailed logging and tracing.

Setup is the mostly the same as above, but you'll instead import `instrument_fastapi` where you define your FastAPI app (usually `main.py`).
```python
# Add this
from iudex import instrument_fastapi

# Find this in your codebase
app = FastAPI()

# Add this
instrument_fastapi(
  app=app,
  service_name=__name__, # or any string describing your service
  env="development", # or any string for your env
)
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
