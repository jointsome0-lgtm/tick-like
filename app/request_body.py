"""Shared bounded request-body admission for JSON endpoints."""
from __future__ import annotations

from fastapi import Request


class PayloadTooLarge(ValueError):
    pass


async def read_capped(request: Request, limit: int) -> bytes:
    """Read at most ``limit`` bytes from the ASGI stream.

    Content-Length is an early refusal only; the streaming count is the
    authority, so chunked requests and dishonest headers cannot make the app
    buffer an oversized body before rejecting it.
    """
    length = request.headers.get("content-length")
    if length is not None:
        try:
            parsed_length = int(length)
        except ValueError as exc:
            raise ValueError("bad Content-Length") from exc
        if parsed_length < 0:
            raise ValueError("bad Content-Length")
        if parsed_length > limit:
            raise PayloadTooLarge(f"request body exceeds {limit} bytes")

    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > limit:
            raise PayloadTooLarge(f"request body exceeds {limit} bytes")
        body.extend(chunk)
    return bytes(body)
