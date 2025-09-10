"""Deprecated WordPress service stub.

This module remains only to satisfy any lingering legacy imports after the
removal of the WordPress integration. All functionality has been removed.
"""

class WordPressService:  # pragma: no cover
    def __init__(self, *_, **__):  # type: ignore
        raise RuntimeError(
            "WordPress integration has been removed. Remove any imports of "
            "'wordpress_service.WordPressService' to finalize migration."
        )

__all__ = ["WordPressService"]