"""AI provider interface. The organizer core only ever talks to this shape -
never to a specific vendor SDK. See docs/PRODUCT_SPEC.md section 10 and
docs/ARCHITECTURE.md section 4.

Contributors adding a new provider (cloud or local) implement AIProvider
and register it; the rest of the app doesn't change.
"""
from __future__ import annotations

from typing import Any, Protocol


class ProviderError(Exception):
    """Raised for provider-level failures (timeout, network, bad credentials)."""


class AIProvider(Protocol):
    @property
    def name(self) -> str:
        """Human-readable provider name, shown in Settings."""
        ...

    @property
    def sends_content_externally(self) -> bool:
        """True if calling suggest() transmits file content off-device.

        Drives the "content may leave this device" disclosure required by
        docs/PRODUCT_SPEC.md section 10 and shown per-action in the review
        popup (section 14.1).
        """
        ...

    def suggest(self, content: str, original_filename: str) -> dict[str, Any]:
        """Return a raw (untrusted) recommendation dict matching the JSON
        contract in docs/PRODUCT_SPEC.md section 11. Callers MUST pass the
        result through organizer.ai.validator before acting on it - this
        method's output is never trusted as-is.

        May raise ProviderError on failure; callers should leave the file
        in need_your_review rather than crash.
        """
        ...
