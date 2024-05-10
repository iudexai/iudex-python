from typing import Optional

from .instrumentation import IudexConfig


def instrument(
    service_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    iudex_api_key: Optional[str] = None,
    config: Optional[IudexConfig] = None,
):
    """Auto-instruments app to send OTel signals to Iudex.

    Invoke this function in your Lambda entrypoint.

    If you use named loggers, instrument them using the returned config object:
    ```python
    my_logger = logging.getLogger("my_logger")
    config = instrument(...)
    config.configure_logger(my_logger)
    ```

    Args:
        service_name: Name of the service, e.g. "billing_service", __name__.
            If not supplied, env var OTEL_SERVICE_NAME will be used.
        instance_id: ID of the service instance, e.g. container id, pod name.
        iudex_api_key: Your Iudex API key.
            If not supplied, env var IUDEX_API_KEY will be used.
        config: IudexConfig object with more granular options.
            Will override all other args, so provide them to the object instead.
    """
    kwargs = {}
    if service_name:
        kwargs["service_name"] = service_name
    if instance_id:
        kwargs["instance_id"] = instance_id
    if iudex_api_key:
        kwargs["iudex_api_key"] = iudex_api_key
    config = config or IudexConfig(**kwargs)

    config.configure()

    return config
