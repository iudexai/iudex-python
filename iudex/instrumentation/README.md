To instrument IUDEX you need to prep 2 things, code and environment variables

# FastAPI

1. Pip install dependencies
```bash
pip install iudex
```
2. Import `instrument_app` where you defined FastAPI (usually `main.py`) from `iudex`
```python
# Add this
from iudex.instrumentation.fastapi_instrumentation import instrument_app

# Find this in your code base
app = FastAPI()

# Add this
instrument_app(app=app, api_key=os.getenv("IUDEX_API_KEY"), service_name=__main__)
```
3. Make sure the app has access to the environment variable `IUDEX_API_KEY`
4. You should be all set! Go to [https://app.iudex.ai/](https://app.iudex.ai/) and enter your API key
5. Go to [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and press `Search` to view your logs


# Lambda / Serverless

1. Pip install dependencies
```bash
pip install iudex
```
2. Import `instrument_app` where you defined FastAPI (usually `main.py`) from `iudex`
```python
# Add this in your lambda function file (likely lambda_function.py)
from iudex.instrumentation.lambda_instrumentation import instrument_app
instrument_app(api_key=os.getenv("IUDEX_API_KEY"), service_name=__main__)
```
3. Make sure the app has access to the environment variable `IUDEX_API_KEY`
4. You should be all set! Go to [https://app.iudex.ai/](https://app.iudex.ai/) and enter your API key
5. Go to [https://app.iudex.ai/logs](https://app.iudex.ai/logs) and press `Search` to view your logs
