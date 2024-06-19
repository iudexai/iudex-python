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

You should be all set! Iudex will now record logs and trace the entire life cycle for each request.

Popular libraries like `openai`, `sqlalchemy`, `supabase`, and more will automatically have specialized metadata like number of tokens or number of rows, etc. captured!

Go to [https://app.iudex.ai/](https://app.iudex.ai/), enter your API key, and start searching your logs and traces!


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
