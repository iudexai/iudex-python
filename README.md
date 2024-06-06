Instrumenting your Python service to send logs to Iudex just takes a few steps.

# FastAPI

1. Pip install dependencies
```bash
pip install iudex
```
2. Import `instrument` where you defined FastAPI (usually `main.py`) from `iudex`
```python
# Add this
from iudex.instrumentation.fastapi import instrument

# Find this in your code base
app = FastAPI()

# Add this
instrument(
  app=app,
  service_name=__name__, # or any string describing your service
  env="development", # or any string for your env
)
```
3. Make sure the app has access to the environment variable `IUDEX_API_KEY`
4. You should be all set! Go to [https://app.iudex.ai/](https://app.iudex.ai/) and enter your API key
5. Go to [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and press `Search` to view your logs


# Lambda / Serverless

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


# Slack Alerts

You can easily configure per-log Slack alerts.

First visit [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and click on the `Add to Slack` button in the top right.

Once installed to your org, tag your logs with the `iudex.slack_channel_id` attribute.
```python
logger.info("Hello from Slack!", extra={"iudex.slack_channel_id": "YOUR_SLACK_CHANNEL_ID"})
```
Your channel ID can be found by clicking the name of the channel in the top left, then at the bottom of the dialog that pops up.

As long as the channel is pubic or you've invited the Iudex app, logs tagged with a specific channel ID will be sent as messages any time they are logged.
