"""Browser-origin checks also protect requests which establish a session."""

from urllib.parse import urlsplit

from aiohttp import web

from config.settings import Settings

from .auth_common import _public_webapp_base_url


def _origin(value: str) -> tuple[str, str, int] | None:
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
            return None
        return (
            parsed.scheme,
            parsed.hostname.lower(),
            parsed.port or (443 if parsed.scheme == "https" else 80),
        )
    except ValueError:
        return None


def _allowed_browser_origins(settings: Settings, request: web.Request) -> set[tuple[str, str, int]]:
    """Origins that may issue browser state-changing requests to the webapp API.

    The public Mini App origin always applies; ``WEBAPP_ADMIN_URL`` allows the
    admin panel to live on a dedicated origin in split deployments.
    """
    origins: set[tuple[str, str, int]] = set()
    candidates = (
        _public_webapp_base_url(settings, request),
        str(getattr(settings, "WEBAPP_ADMIN_URL", "") or "").strip(),
    )
    for candidate in candidates:
        parsed = _origin(candidate) if candidate else None
        if parsed is not None:
            origins.add(parsed)
    return origins


def browser_origin_allowed(request: web.Request, settings: Settings) -> bool:
    origin = request.headers.get("Origin")
    referer = request.headers.get("Referer")
    if origin is not None or referer is not None:
        received = _origin(origin if origin is not None else referer or "")
        return received is not None and received in _allowed_browser_origins(settings, request)
    return request.headers.get("Sec-Fetch-Site", "") not in {"cross-site", "same-site"}


def browser_origin_present(request: web.Request) -> bool:
    return bool(
        request.headers.get("Origin")
        or request.headers.get("Referer")
        or request.headers.get("Sec-Fetch-Site") == "same-origin"
    )
