import importlib
import importlib.util
import importlib.metadata
from packaging.requirements import Requirement
import logging

logger = logging.getLogger(__name__)


def maybe_instrument_lib(module_path: str, instrumentor_class_name: str, **kwargs):
    try:
        # get instrumentor and its requirements
        package = "iudex" if module_path[0] == "." else None
        module = importlib.import_module(module_path, package)

        construct_instrumentor = getattr(module, instrumentor_class_name)
        instrumentor = construct_instrumentor(**kwargs)
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
            logger.info(
                f"Skipping {instrumentor_class_name} instrmentation as it was already instrumented."
            )
            return

        # instrument the library
        instrumentor.instrument()

    # instrumentor tried and failed to import a requirement, so swallow error and skip
    except ModuleNotFoundError as e:
        logger.debug(f"Skipping {instrumentor_class_name} instrumentation: {e}")

    # edge case when AwsLambdaInstrumentor tries to rsplit on non-existent handler name
    except AttributeError as e:
        if str(e) == "'NoneType' object has no attribute 'rsplit'":
            logger.debug(f"Skipping {instrumentor_class_name} instrumentation: {e}")
            return
        raise e

    except Exception as e:
        logger.exception(f"Failed to instrument with {instrumentor_class_name}: {e}")
