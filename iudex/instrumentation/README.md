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
from iudex.instrumentation.lambda import instrument
instrument(
  service_name=__name__, # or any string describing your service
  env="development", # or any string for your env
)
```
3. Make sure the app has access to the environment variable `IUDEX_API_KEY`
4. You should be all set! Go to [https://app.iudex.ai/](https://app.iudex.ai/) and enter your API key
5. Go to [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and press `Search` to view your logs
