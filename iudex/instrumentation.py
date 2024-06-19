import logging
from typing import Optional, Union

from .config import IudexConfig, _IudexConfig
from .utils import maybe_instrument_lib

logger = logging.getLogger(__name__)

INSTRUMENTATION_LIBS = [
    # iudex custom
    (
        ".openai",
        "OpenAIInstrumentor",
        {
            "enrich_assistant": True,
            "enrich_token_usage": True,
            "exception_logger": logger.error,
        },
    ),
    (".supabase", "SupabaseInstrumentor", {}),

    # opentelemetry-python-contrib
    # NOTE: these are excluded because they are already instrumented by higher level libs
    # - asgi
    # - dbapi
    # - starlette
    # - wsgi
    ("opentelemetry.instrumentation.aio_pika", "AioPikaInstrumentor", {}),
    ("opentelemetry.instrumentation.aiohttp_client", "AioHttpClientInstrumentor", {}),
    # broken: https://github.com/open-telemetry/opentelemetry-python-contrib/issues/2053
    # ("opentelemetry.instrumentation.aiohttp_server", "AioHttpServerInstrumentor", {}),
    ("opentelemetry.instrumentation.aiopg", "AiopgInstrumentor", {}),
    ("opentelemetry.instrumentation.asyncio", "AsyncioInstrumentor", {}),
    ("opentelemetry.instrumentation.asyncpg", "AsyncpgInstrumentor", {}),
    ("opentelemetry.instrumentation.aws_lambda", "AwsLambdaInstrumentor", {}),
    ("opentelemetry.instrumentation.boto", "BotoInstrumentor", {}),
    ("opentelemetry.instrumentation.boto3sqs", "Boto3SQSInstrumentor", {}),
    ("opentelemetry.instrumentation.botocore", "BotocoreInstrumentor", {}),
    ("opentelemetry.instrumentation.cassandra", "CassandraInstrumentor", {}),
    ("opentelemetry.instrumentation.celery", "CeleryInstrumentor", {}),
    ("opentelemetry.instrumentation.confluent_kafka", "ConfluentKafkaInstrumentor", {}),
    ("opentelemetry.instrumentation.django", "DjangoInstrumentor", {}),
    ("opentelemetry.instrumentation.elasticsearch", "ElasticsearchInstrumentor", {}),
    ("opentelemetry.instrumentation.falcon", "FalconInstrumentor", {}),
    ("opentelemetry.instrumentation.flask", "FlaskInstrumentor", {}),
    ("opentelemetry.instrumentation.grpc", "GrpcInstrumentor", {}),
    ("opentelemetry.instrumentation.httpx", "HTTPXClientInstrumentor", {}),
    ("opentelemetry.instrumentation.jinja2", "Jinja2Instrumentor", {}),
    ("opentelemetry.instrumentation.kafka_python", "KafkaPythonInstrumentor", {}),
    ("opentelemetry.instrumentation.logging", "LoggingInstrumentor", {}),
    ("opentelemetry.instrumentation.mysql", "MySQLInstrumentor", {}),
    ("opentelemetry.instrumentation.mysqlclient", "MySQLclientInstrumentor", {}),
    ("opentelemetry.instrumentation.pika", "PikaInstrumentor", {}),
    ("opentelemetry.instrumentation.psycopg", "PsycopgInstrumentor", {}),
    ("opentelemetry.instrumentation.psycopg2", "Psycopg2Instrumentor", {}),
    ("opentelemetry.instrumentation.pymemcache", "PymemcacheInstrumentor", {}),
    ("opentelemetry.instrumentation.pymongo", "PymongoInstrumentor", {}),
    ("opentelemetry.instrumentation.pymysql", "PymysqlInstrumentor", {}),
    ("opentelemetry.instrumentation.pyramid", "PyramidInstrumentor", {}),
    ("opentelemetry.instrumentation.redis", "RedisInstrumentor", {}),
    ("opentelemetry.instrumentation.remoulade", "RemouladeInstrumentor", {}),
    ("opentelemetry.instrumentation.requests", "RequestsInstrumentor", {}),
    ("opentelemetry.instrumentation.sklearn", "SklearnInstrumentor", {}),
    (
        "opentelemetry.instrumentation.sqlalchemy",
        "SQLAlchemyInstrumentor",
        {"enable_commenter": True},
    ),
    ("opentelemetry.instrumentation.sqlite3", "SQLite3Instrumentor", {}),
    ("opentelemetry.instrumentation.system_metrics", "SystemMetricsInstrumentor", {}),
    ("opentelemetry.instrumentation.threading", "ThreadingInstrumentor", {}),
    ("opentelemetry.instrumentation.tornado", "TornadoInstrumentor", {}),
    ("opentelemetry.instrumentation.tortoiseorm", "TortoiseORMInstrumentor", {}),
    ("opentelemetry.instrumentation.urllib", "URLLibInstrumentor", {}),
    ("opentelemetry.instrumentation.urllib3", "URLLib3Instrumentor", {}),

    # openllmetry
    ("opentelemetry.instrumentation.alephalpha", "AlephAlphaInstrumentor", {}),
    ("opentelemetry.instrumentation.anthropic", "AnthropicInstrumentor", {}),
    ("opentelemetry.instrumentation.bedrock", "BedrockInstrumentor", {}),
    ("opentelemetry.instrumentation.chromadb", "ChromaDBInstrumentor", {}),
    ("opentelemetry.instrumentation.cohere", "CohereInstrumentor", {}),
    ("opentelemetry.instrumentation.google_generativeai", "GoogleGenerativeAiInstrumentor", {}),
    ("opentelemetry.instrumentation.haystack", "HaystackInstrumentor", {}),
    ("opentelemetry.instrumentation.langchain", "LangChainInstrumentor", {}),
    ("opentelemetry.instrumentation.llamaindex", "LlamaIndexInstrumentor", {}),
    ("opentelemetry.instrumentation.milvus", "MilvusInstrumentor", {}),
    ("opentelemetry.instrumentation.mistralai", "MistralAIInstrumentor", {}),
    ("opentelemetry.instrumentation.ollama", "OllamaInstrumentor", {}),
    ("opentelemetry.instrumentation.pinecone", "PineconeInstrumentor", {}),
    ("opentelemetry.instrumentation.qdrant", "QdrantInstrumentor", {}),
    ("opentelemetry.instrumentation.replicate", "ReplicateInstrumentor", {}),
    ("opentelemetry.instrumentation.together", "TogetherAiInstrumentor", {}),
    ("opentelemetry.instrumentation.transformers", "TransformersInstrumentor", {}),
    ("opentelemetry.instrumentation.vertexai", "VertexAIInstrumentor", {}),
    ("opentelemetry.instrumentation.watsonx", "WatsonxInstrumentor", {}),
    ("opentelemetry.instrumentation.weaviate", "WeaviateInstrumentor", {})
]


def instrument(
    service_name: Optional[str] = None,
    instance_id: Optional[str] = None,
    iudex_api_key: Optional[str] = None,
    log_level: Optional[Union[int, str]] = None,
    git_commit: Optional[str] = None,
    github_url: Optional[str] = None,
    env: Optional[str] = None,
    config: Optional[IudexConfig] = None,
):
    """Auto-instruments app to send OTel signals to Iudex.

    Invoke this function in your app entrypoint.

    Args:
        service_name: Name of the service, e.g. "billing_service", __name__.
            If not supplied, env var OTEL_SERVICE_NAME will be used.
        instance_id: ID of the service instance, e.g. container id, pod name.
        iudex_api_key: Your Iudex API key.
            If not supplied, env var IUDEX_API_KEY will be used.
        log_level: Logging level for the root logger.
        git_commit: Commit hash of the currently deployed code.
            Used with github_url to deep link telemetry to source code.
        github_url: URL of the GitHub repository.
            Used with git_commit to deep link telemetry to source code.
        env: Environment of the service, e.g. "production", "staging".
        config: IudexConfig object with more granular options.
            Will override all other args, so provide them to the object instead.
    """
    config = config or {
        "iudex_api_key": iudex_api_key,
        "service_name": service_name,
        "instance_id": instance_id,
        "logs_endpoint": None,
        "traces_endpoint": None,
        "log_level": log_level,
        "git_commit": git_commit,
        "github_url": github_url,
        "env": env,
    }
    iudex_config = _IudexConfig(**config)
    iudex_config.configure()

    for module_path, instrumentor_class_name, kwargs in INSTRUMENTATION_LIBS:
        maybe_instrument_lib(module_path, instrumentor_class_name, **kwargs)

    return iudex_config
