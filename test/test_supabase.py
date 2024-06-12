import os
import pytest
from supabase import create_client, Client
from iudex.supabase import SupabaseInstrumentor

@pytest.fixture
def supabase_instrumentor():
    supabase_url = os.getenv("SUPABASE_URL", "https://xyzcompany.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "public-anon-key")
    return SupabaseInstrumentor(supabase_url, supabase_key)

def test_instrument_supabase(supabase_instrumentor):
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
    with pytest.raises(Exception):
        SupabaseInstrumentor("invalid_url", "public-anon-key")

def test_invalid_supabase_key():
    with pytest.raises(Exception):
        SupabaseInstrumentor("https://xyzcompany.supabase.co", "invalid_key")

def test_missing_environment_variables(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    with pytest.raises(Exception):
        SupabaseInstrumentor(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def test_autoinstrumentation(supabase_instrumentor):
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
    assert "telemetry" in config  # Example check, adjust based on actual implementation
