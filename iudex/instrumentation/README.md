To instrument IUDEX you need to prep 2 things, code and environment variables

# FastAPI

1. Pip install dependencies
```bash
pip install opentelemetry-distro opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp-proto-http
```
2. Create a new file called iudex_instrumentation.py
3. Add to that file
```python
import logging
import os

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or "https://hsyrgkn5ja.execute-api.us-west-2.amazonaws.com/resource_logs"
api_key = os.getenv("IUDEX_API_KEY")

configured = False
def configure(service_name: str | None, instance_id: str | None):
    global configured
    if (configured):
        return
    resource = Resource.create({
        "service.name": service_name,
        "service.instance.id": instance_id,
    })
    logger_provider = LoggerProvider(resource)
    set_logger_provider(logger_provider)

    exporter = OTLPLogExporter(endpoint=endpoint, headers={ "x-api-key": api_key })
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    logging.basicConfig(level=logging.NOTSET)
    logging.getLogger().addHandler(LoggingHandler())
    configured = True

def instrument_app(app, service_name: str | None = None, instance_id: str | None = None):
    configure(service_name, instance_id)
    FastAPIInstrumentor().instrument_app(app)
```
4. Import `instrument_app` where you defined FastAPI (usually `main.py`)
5. After the line `app = FastAPI()`, add `instrument_app(app, <<service_name>>)`
6. Make sure the app has access to the environment variable `IUDEX_API_KEY`
