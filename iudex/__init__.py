# ruff: noqa: E402
# ^ because monkeypatches must import and run before other imports
from .monkeypatches.encode_value import monkeypatch_encode_value

monkeypatch_encode_value()

from .config import IudexConfig, configure_logger
from .instrumentation import instrument
from .fastapi import instrument_fastapi
from .trace import trace, trace_lambda, traced_fn

__all__ = ["IudexConfig", "configure_logger", "instrument", "instrument_fastapi", "trace", "trace_lambda", "traced_fn"]
