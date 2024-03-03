from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Iudex


class ApiResource:
    _client: Iudex

    def __init__(self, client: Iudex) -> None:
        self._client = client
