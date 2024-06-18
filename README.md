# Iudex

Next generation observability.


### Table of contents
- [Iudex](#iudex)
    - [Table of contents](#table-of-contents)
- [Getting Started](#getting-started)
    - [FastAPI](#fastapi)
    - [Lambda](#lambda)
    - [Custom Functions](#custom-functions)
- [Slack Alerts](#slack-alerts)


# Getting Started
Instrumenting your Python service to send logs to Iudex just takes a few steps.

1. Pip install dependencies
```bash
pip install iudex
```
2. At the top of your entrypoint (usually `main.py`), import `instrument` from `iudex` and invoke it.
```python
from iudex.instrumentation import instrument
instrument(
  service_name=__name__, # or any string describing your service
  env="production", # or any string for your env
)
```
3. Make sure the app has access to the environment variable `IUDEX_API_KEY`
4. You should be all set! Go to [https://app.iudex.ai/](https://app.iudex.ai/) and enter your API key
5. Go to [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and press `Search` to view your logs


### FastAPI
If you use FastAPI, we highly recommend instrumenting your app for even more detailed logging and tracing.

Setup is the mostly the same as above, but you'll instead import `instrument_fastapi` where you define your FastAPI app (usually `main.py`) at the top of your file.
```python
# Add this
from iudex import instrument_fastapi

# Find this in your codebase
app = FastAPI()

# Add this
instrument_fastapi(
  app=app,
  service_name=__name__, # or any string describing your service
  env="production", # or any string for your env
)
```


### Lambda
If you use lambdas, we recommend instrumenting and adding tracing to your handlers.

1. Add this to the top of your handler file
```python
from iudex import instrument, trace_lambda
instrument(
  app=app,
  service_name=__name__, # or any string describing your service
  env="production", # or any string for your env
)
```

2. Add the decorator to the lambda handler
```python
@trace_lambda(name="name_of_my_lambda")
def lambda_handler(event, context):
  pass
```


### Custom Functions
We recommend that you trace important functions in your code base that would be helpful to see when following a stack trace. It is required to call `instrument` earlier in the code before the traced function is invoked.

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
