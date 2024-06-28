import modal
from modal import Image

image = (
    Image.debian_slim(python_version="3.10")
    .pip_install("iudex")
)

app = modal.App("example-get-started")

@app.function(image=image, secrets=[modal.Secret.from_name("iudex-api-key")])
def square(x):
    import logging
    from iudex import instrument

    instrument(service_name="test-modal-instrumentation", env="drake-local")

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("This code is running on a remote worker!")
    return x**2


@app.local_entrypoint()
def main():
    print("the square is %s" % square.remote(42))
