"""Vercel Serverless Function entry point for FastAPI."""

import os
import sys

# Ensure backend root is on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app as fastapi_app  # noqa: E402


async def app(scope, receive, send):
    """ASGI wrapper to correct request path rewritten by Vercel."""
    if scope["type"] in ("http", "websocket"):
        headers = dict(scope.get("headers", []))

        # Check for original client path in Vercel edge proxy headers
        original_path = None
        for header_key in (b"x-matched-path", b"x-forwarded-uri", b"x-original-uri"):
            if header_key in headers:
                val = headers[header_key].decode("utf-8")
                # Ignore if it points directly to the rewritten lambda file
                if not val.startswith("/api/index.py"):
                    original_path = val.split("?")[0]
                    break

        if original_path:
            scope["path"] = original_path
            scope["raw_path"] = original_path.encode("utf-8")
        else:
            # Strip rewrite destination prefixes if passed as request path
            path = scope.get("path", "")
            if path.startswith("/api/index.py"):
                stripped = path[len("/api/index.py"):]
                scope["path"] = stripped if stripped.startswith("/") else ("/" + stripped if stripped else "/")
                scope["raw_path"] = scope["path"].encode("utf-8")
            elif path.startswith("/api/") and not path.startswith("/api/routes"):
                stripped = path[len("/api"):]
                scope["path"] = stripped
                scope["raw_path"] = stripped.encode("utf-8")

    await fastapi_app(scope, receive, send)
