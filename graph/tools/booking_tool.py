"""Standalone Booking Tool draft for the proposed Revy CRM contract."""

import json
import re
from datetime import datetime
from http.client import HTTPSConnection, HTTPException
from typing import Literal, TypedDict
from urllib.parse import urlsplit


class BookingResult(TypedDict, total=False):
    outcome: Literal["scheduled", "invalid_input", "rejected", "unknown", "configuration_error"]
    id: int
    http_status: int
    field: str


def create_booking(
    phone_number: str,
    start_at: str,
    type: Literal["call", "meeting"],
    description: str | None = None,
    *,
    endpoint: str,
    token: str,
    timeout: float = 10.0,
) -> BookingResult:
    """Submit one request using a trusted, configured HTTPS endpoint."""
    if not re.fullmatch(r"\+[1-9][0-9]{1,14}", phone_number):
        return {"outcome": "invalid_input", "field": "phone_number"}
    if type not in ("call", "meeting"):
        return {"outcome": "invalid_input", "field": "type"}
    try:
        requested_time = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
        if requested_time.utcoffset() is None:
            raise ValueError("A timezone offset is required")
    except ValueError:
        return {"outcome": "invalid_input", "field": "start_at"}

    try:
        url = urlsplit(endpoint)
        port = url.port
    except ValueError:
        return {"outcome": "configuration_error"}
    if (
        url.scheme != "https" or not url.hostname or not url.path
        or url.fragment or url.username is not None or not token.strip()
    ):
        return {"outcome": "configuration_error"}

    payload = {
        "phone_number": phone_number,
        "start_at": requested_time.isoformat(),
        "type": type,
        "source": "agent",
    }
    if description is not None:
        payload["description"] = description

    target = url.path
    if url.query:
        target += "?" + url.query

    connection = HTTPSConnection(url.hostname, port, timeout=timeout)
    try:
        connection.request(
            "POST",
            target,
            body=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response = connection.getresponse()
        if 400 <= response.status < 500 and response.status != 408:
            return {"outcome": "rejected", "http_status": response.status}
        if response.status != 201:
            return {"outcome": "unknown", "http_status": response.status}
        booking = json.loads(response.read())
    except (OSError, HTTPException, ValueError):
        return {"outcome": "unknown"}
    finally:
        connection.close()

    if isinstance(booking, dict) and booking.get("status") == "scheduled":
        booking_id = booking.get("id")
        if booking_id.__class__ is int and booking_id > 0:
            return {"outcome": "scheduled", "id": booking_id}
    return {"outcome": "unknown", "http_status": 201}
