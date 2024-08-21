from iudex import instrument
from iudex.trace import trace

iudex_config = instrument(
    service_name="joke-service",
    env="prod",
    iudex_api_key="",
)

from guardrails import Guard
from guardrails.telemetry import default_otlp_tracer
from guardrails.hub import ValidLength

default_otlp_tracer('joke_guard')

@trace
def tell_joke(subject):
    if not subject:
        raise ValueError("I can't tell a joke without a subject!")

    guard = Guard(name="joke_guard").use_many(
        ValidLength(min=0, max=100),
    )

    res = guard(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Tell me a joke about {subject}",
        }],
        temperature=1,
    )

    # subject="space" => "Why did the sun go to school? To get a little brighter!"
    return res.validated_output

if __name__ == "__main__":
    print(tell_joke("space"))
