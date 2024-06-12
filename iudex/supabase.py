import logging
from typing import Optional, Union

from supabase import create_client, Client

from .instrumentation import IudexConfig
from .instrumentation import instrument as _instrument

logger = logging.getLogger(__name__)

class SupabaseInstrumentor:
    """
    A class to auto-instrument Supabase client to send OpenTelemetry (OTel) signals to Iudex.

    Attributes:
        supabase_url (str): The URL of the Supabase instance.
        supabase_key (str): The API key for the Supabase instance.
        client (Optional[Client]): The Supabase client instance.

    Methods:
        instrument_supabase(service_name, instance_id, iudex_api_key, log_level, git_commit, github_url, env, config):
            Auto-instruments Supabase client to send OTel signals to Iudex.
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initializes the SupabaseInstrumentor with the given Supabase URL and API key.

        Args:
            supabase_url (str): The URL of the Supabase instance.
            supabase_key (str): The API key for the Supabase instance.
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None

    def instrument_supabase(
        self,
        service_name: Optional[str] = None,
        instance_id: Optional[str] = None,
        iudex_api_key: Optional[str] = None,
        log_level: Optional[Union[int, str]] = None,
        git_commit: Optional[str] = None,
        github_url: Optional[str] = None,
        env: Optional[str] = None,
        config: Optional[IudexConfig] = None,
    ) -> IudexConfig:
        """
        Auto-instruments Supabase client to send OTel signals to Iudex.

        Invoke this function to instrument Supabase client.

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

        Returns:
            IudexConfig: The configuration object used for instrumentation.
        """
        iudex_config = _instrument(
            service_name=service_name,
            instance_id=instance_id,
            iudex_api_key=iudex_api_key,
            log_level=log_level,
            git_commit=git_commit,
            github_url=github_url,
            env=env,
            config=config,
        )

        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            return iudex_config
        except Exception as e:
            logger.error(f"Error initializing Supabase instrumentor: {e}")

        return iudex_config
