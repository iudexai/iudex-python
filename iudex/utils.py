import importlib
import importlib.metadata
import importlib.util
import logging
import os
from typing import Any

from packaging.requirements import Requirement

from .asgi import client_request_hook, client_response_hook

logger = logging.getLogger(__name__)


ASGI_INSTRUMENTORS = ["FastAPIInstrumentor"]


def maybe_instrument_lib(
    module_path: str,
    instrumentor_class_name: str,
    constructor_kwargs: dict[str, Any],
    instrument_kwargs: dict[str, Any],
):
    try:
        # skip lambda warnings
        if instrumentor_class_name == "AwsLambdaInstrumentor":
            lambda_handler = os.environ.get("ORIG_HANDLER", os.environ.get("_HANDLER"))
            if not lambda_handler:
                return

        # add req/res payload hooks
        # TODO: support this through .instrument args too
        disable_req_res_tracing = os.getenv("DISABLE_REQ_RES_TRACING", False)
        if not disable_req_res_tracing and instrumentor_class_name in ASGI_INSTRUMENTORS:
            instrument_kwargs["client_request_hook"] = client_request_hook
            instrument_kwargs["client_response_hook"] = client_response_hook

        # get instrumentor and its requirements
        package = "iudex" if module_path[0] == "." else None
        module = importlib.import_module(module_path, package)

        construct_instrumentor = getattr(module, instrumentor_class_name)
        instrumentor = construct_instrumentor(**constructor_kwargs)
        req_strs = instrumentor.instrumentation_dependencies()
        reqs = [Requirement(r) for r in req_strs]

        # check package requirements are satisfied
        for req in reqs:
            package_name = req.name

            if importlib.util.find_spec(package_name) is None:
                logger.debug(
                    f"Skipping {instrumentor_class_name} instrumentation as requirement {req.name} is not installed."
                )
                return

            package_version = importlib.metadata.version(package_name)
            if package_version not in req.specifier:
                raise ValueError(
                    f"Version {package_version} of {package_name} does not satisfy the requirement {req}."
                )

        if instrumentor.is_instrumented_by_opentelemetry:
            logger.debug(
                f"Skipping {instrumentor_class_name} instrumentation as it was already instrumented."
            )
            return

        # instrument the library
        instrumentor.instrument(**instrument_kwargs)

    # instrumentor tried and failed to import a requirement, so swallow error and skip
    except ModuleNotFoundError as e:
        logger.debug(f"Skipping {instrumentor_class_name} instrumentation: {e}")

    # edge case when AwsLambdaInstrumentor tries to rsplit on non-existent handler name
    except AttributeError as e:
        if str(e) == "'NoneType' object has no attribute 'rsplit'":
            logger.debug(f"Skipping {instrumentor_class_name} instrumentation: {e}")
            return
        logger.exception(f"Failed to instrument with {instrumentor_class_name}: {e}")

    except Exception as e:
        logger.exception(f"Failed to instrument with {instrumentor_class_name}: {e}")
