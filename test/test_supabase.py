import os
import pytest
from supabase import create_client, Client
from supabase._sync.client import SupabaseException
from iudex.supabase import SupabaseInstrumentor
from unittest.mock import patch, MagicMock
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

@pytest.fixture
def supabase_instrumentor():
    supabase_url = os.getenv("SUPABASE_URL", "https://xyzcompany.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "public-anon-key")
    return SupabaseInstrumentor(supabase_url, supabase_key)

@pytest.fixture
def tracer_provider():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider, exporter

@patch('supabase.create_client')
def test_instrument_supabase(mock_create_client, supabase_instrumentor):
    mock_client = MagicMock(spec=Client)
    with patch.object(Client, '__init__', lambda self, supabase_url, supabase_key, options=None: None):
        mock_create_client.return_value = mock_client
        config = supabase_instrumentor.instrument_supabase(
            service_name="test_service",
            instance_id="test_instance",
            iudex_api_key="test_api_key",
            log_level="DEBUG",
            git_commit="test_commit",
            github_url="https://github.com/test/repo",
            env="test_env"
        )
        assert config is not None
        assert supabase_instrumentor.client is not None
        assert isinstance(supabase_instrumentor.client, Client)

def test_invalid_supabase_url():
    instrumentor = SupabaseInstrumentor("invalid_url", "public-anon-key")
    with pytest.raises(SupabaseException, match="Invalid URL"):
        instrumentor.instrument_supabase()

def test_invalid_supabase_key():
    instrumentor = SupabaseInstrumentor("https://xyzcompany.supabase.co", "invalid_key")
    with pytest.raises(SupabaseException, match="Invalid API key"):
        instrumentor.instrument_supabase()

def test_missing_environment_variables(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    instrumentor = SupabaseInstrumentor(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    with pytest.raises(SupabaseException, match="supabase_url is required"):
        instrumentor.instrument_supabase()

@patch('supabase.create_client')
def test_autoinstrumentation(mock_create_client, supabase_instrumentor):
    mock_client = MagicMock(spec=Client)
    with patch.object(Client, '__init__', lambda self, supabase_url, supabase_key, options=None: None):
        mock_create_client.return_value = mock_client
        # Assuming the instrument_supabase method sets up some telemetry data
        config = supabase_instrumentor.instrument_supabase(
            service_name="test_service",
            instance_id="test_instance",
            iudex_api_key="test_api_key",
            log_level="DEBUG",
            git_commit="test_commit",
            github_url="https://github.com/test/repo",
            env="test_env"
        )
        assert config is not None  # Example check, adjust based on actual implementation

@patch('supabase.create_client')
def test_trace_wrapper(mock_create_client, supabase_instrumentor, tracer_provider):
    mock_client = MagicMock(spec=Client)
    mock_client._postgrest = None
    mock_client.rest_url = "http://localhost:8000"  # Set the rest_url attribute
    mock_client.headers = {"Authorization": "Bearer test_key"}
    mock_client.schema = "public"
    mock_client.postgrest_client_timeout = 60
    mock_client.options = MagicMock()
    mock_client.options.headers = mock_client.headers
    mock_client.options.schema = mock_client.schema
    mock_client.options.postgrest_client_timeout = mock_client.postgrest_client_timeout
    def postgrest_side_effect():
        print("Accessing postgrest property")
        if mock_client._postgrest is None:
            print("Initializing _postgrest attribute")
            mock_client._postgrest = MagicMock()
            mock_client._postgrest.from_.return_value = MagicMock()  # Ensure _postgrest is not None and has a from_ method
        return mock_client._postgrest
    mock_client.postgrest = property(postgrest_side_effect)
    with patch.object(Client, '__init__', lambda self, supabase_url, supabase_key, options=None: setattr(self, 'rest_url', f"{supabase_url}/rest/v1") or setattr(self, '_postgrest', None) or setattr(self, 'options', mock_client.options)):
        mock_create_client.return_value = mock_client
        supabase_instrumentor.instrument_supabase(
            service_name="test_service",
            instance_id="test_instance",
            iudex_api_key="test_api_key",
            log_level="DEBUG",
            git_commit="test_commit",
            github_url="https://github.com/test/repo",
            env="test_env"
        )
        client = supabase_instrumentor.client
        # Explicitly access the postgrest property to trigger lazy initialization
        _ = client.postgrest
        assert client.postgrest is not None  # Ensure postgrest is not None
        print("Calling client.from_")
        client.from_("test_table").select("*")
        print("Called client.from_")
        provider, exporter = tracer_provider
        print("Accessing tracer provider and exporter")
        spans = exporter.get_finished_spans()
        print(f"Number of spans recorded: {len(spans)}")
        if spans:
            span = spans[0]
            print(f"Span name: {span.name}")
            print(f"Span attributes: {span.attributes}")
            assert span.name == "from_"
            assert span.attributes["arg_0"] == "test_table"
