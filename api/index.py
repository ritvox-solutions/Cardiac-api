"""Vercel Serverless Function entry point for FastAPI."""

import os
import sys
from urllib.parse import parse_qs, urlencode

# Ensure backend root is on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app as fastapi_app  # noqa: E402


async def app(scope, receive, send):
    """ASGI wrapper to correct request path rewritten by Vercel."""
    if scope["type"] in ("http", "websocket"):
        raw_qs = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(raw_qs, keep_blank_values=True)

        if "__path" in params:
            p = params.pop("__path")[0]
            corrected_path = "/" + p.lstrip("/")
            scope["path"] = corrected_path
            scope["raw_path"] = corrected_path.encode("utf-8")
            remaining_qs = urlencode(params, doseq=True)
            scope["query_string"] = remaining_qs.encode("utf-8")
        else:
            headers = dict(scope.get("headers", []))
            for hk in (b"x-matched-path", b"x-forwarded-uri", b"x-original-uri"):
                if hk in headers:
                    val = headers[hk].decode("utf-8")
                    if not val.startswith("/api/index.py") and not val.startswith("/api/"):
                        path = val.split("?")[0]
                        scope["path"] = "/" + path.lstrip("/")
                        scope["raw_path"] = scope["path"].encode("utf-8")
                        break

    await fastapi_app(scope, receive, send)
