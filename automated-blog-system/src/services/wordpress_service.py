"""Deprecated WordPress service stub.

WordPress integration was removed; the system now publishes via Ghost
(see services/ghost_service.py). This stub remains only to surface a clear
error for any lingering legacy imports.
"""

class WordPressService:  # pragma: no cover
    def __init__(self, *_, **__):  # type: ignore
        raise RuntimeError(
            "WordPress integration has been removed. "
            "Use src.services.ghost_service.GhostService instead."
        )


__all__ = ["WordPressService"]
