"""Bound body size before multipart spooling or JSON parsing."""

from fastapi import HTTPException
from starlette.responses import JSONResponse


class RequestSizeLimit:
    def __init__(self, app, max_bytes=12 * 1024 * 1024):
        self.app = app
        self.maximum = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = 0
        if declared > self.maximum:
            return await JSONResponse(
                {"error": {"code": 413, "message": "Request exceeds 12 MiB"}}, status_code=413
            )(scope, receive, send)
        consumed = 0

        async def bounded():
            nonlocal consumed
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > self.maximum:
                    raise HTTPException(413, "Request exceeds 12 MiB")
            return message

        return await self.app(scope, bounded, send)
