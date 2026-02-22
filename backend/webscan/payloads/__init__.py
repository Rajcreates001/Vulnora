"""Payload sets for deterministic vulnerability testing."""

from webscan.payloads.payloads import (
    SQLI_PAYLOADS,
    XSS_PAYLOADS,
    CMD_INJECTION_PAYLOADS,
    PATH_TRAVERSAL_PAYLOADS,
    OPEN_REDIRECT_PAYLOADS,
    get_payloads_for_category,
)

__all__ = [
    "SQLI_PAYLOADS",
    "XSS_PAYLOADS",
    "CMD_INJECTION_PAYLOADS",
    "PATH_TRAVERSAL_PAYLOADS",
    "OPEN_REDIRECT_PAYLOADS",
    "get_payloads_for_category",
]
