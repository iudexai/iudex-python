import os
import logging

from openai import OpenAI
from supabase import Client, create_client

from iudex import instrument

instrument(service_name="test_supabase_instrumentation")

logger = logging.getLogger(__name__)

client = OpenAI()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
if not url or not key:
    raise ValueError(
        "Please set the SUPABASE_URL and SUPABASE_KEY environment variables"
    )
supabase: Client = create_client(url, key)


def main():
    logger.info("Starting test_supabase_instrumentation")
    logger.info("Creating chat")
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "tell me a joke involving supabase and opentelemetry!",
            }
        ],
    )
    content = res.choices[0].message.content
    logger.info(f"Storing LLM response: {content}")
    supabase.table("chat").insert({"message": content}).execute()
    logger.info("Fetching chat")
    supabase.table("chat").select("*").execute()
    logger.info("Finished test_supabase_instrumentation")


if __name__ == "__main__":
    main()
