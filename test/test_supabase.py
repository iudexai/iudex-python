import os
import pytest
from supabase import create_client, Client
from supabase._sync.client import SupabaseException
from iudex.supabase import SupabaseInstrumentor
from unittest.mock import patch, MagicMock

@pytest.fixture
def supabase_instrumentor():
    supabase_url = os.getenv("SUPABASE_URL", "https://xyzcompany.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "public-anon-key")
    return SupabaseInstrumentor(supabase_url, supabase_key)

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
