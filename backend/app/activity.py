"""Live activity log: one readable line per API call, for debugging and demos.

Every request is printed to stdout (so it shows up in the Render logs) like:

    10:42:31  POST   /orders                     201   61ms  umar (STUDENT)  Order ORD-20261024-0007 placed ...

and kept in a small in-memory buffer that the admin's live page (/admin/live) reads.
Passwords, tokens and request bodies are never logged. Logging can never break a request.
"""
import logging
import sys
import threading
import time
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

IST = timezone(timedelta(hours=5, minutes=30))

# Health checks (Render, UptimeRobot) and the live page's own polling would drown everything else.
QUIET_PATHS = {"/", "/favicon.ico", "/openapi.json", "/admin/live", "/admin/live/feed"}
BUFFER_SIZE = 500

log = logging.getLogger("canteen.activity")

# Per-request scratchpad. Endpoints run in a worker thread with a copy of the context,
# so values are written into this shared dict rather than by setting the variable.
_current: ContextVar[Optional[dict]] = ContextVar("canteen_activity", default=None)

_buffer: deque = deque(maxlen=BUFFER_SIZE)
_lock = threading.Lock()
_next_id = 1


def setup_logging() -> None:
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
        log.propagate = False
    # This log replaces uvicorn's shorter access line.
    logging.getLogger("uvicorn.access").disabled = True


def _ctx() -> Optional[dict]:
    return _current.get()


def set_user(user) -> None:
    """Record who is making the current request (called once they are authenticated)."""
    ctx = _ctx()
    if ctx is not None and user is not None:
        ctx["user"] = user.username
        ctx["role"] = user.role.name


def event(message: str) -> None:
    """Describe what the current request did, e.g. "Order ORD-... placed, ₹160"."""
    ctx = _ctx()
    if ctx is not None:
        ctx["events"].append(message)


def _record(entry: dict) -> None:
    global _next_id
    with _lock:
        entry["id"] = _next_id
        _next_id += 1
        _buffer.append(entry)


def recent(after: int = 0, limit: int = 200) -> List[Dict]:
    with _lock:
        items = [e for e in _buffer if e["id"] > after]
    return items[-limit:]


def _format(e: dict) -> str:
    who = f"{e['user']} ({e['role']})" if e["user"] else "-"
    line = f"{e['time']}  {e['method']:<6} {e['path']:<34} {e['status']:>3} {e['ms']:>5}ms  {who}"
    if e["detail"]:
        line += f"  {e['detail']}"
    return line


async def activity_middleware(request: Request, call_next):
    path = request.url.path
    if path in QUIET_PATHS or request.method == "OPTIONS":
        return await call_next(request)

    ctx = {"user": None, "role": None, "events": [], "error": None}
    token = _current.set(ctx)
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        ctx["error"] = f"server error: {type(exc).__name__}"
        raise
    finally:
        _current.reset(token)
        try:
            query = f"?{request.url.query}" if request.url.query else ""
            entry = {
                "time": datetime.now(IST).strftime("%H:%M:%S"),
                "method": request.method,
                "path": path + query,
                "status": status_code,
                "ms": round((time.perf_counter() - start) * 1000),
                "user": ctx["user"],
                "role": ctx["role"],
                "detail": "; ".join(ctx["events"] + ([ctx["error"]] if ctx["error"] else [])),
            }
            _record(entry)
            log.info(_format(entry))
        except Exception:  # never let logging break the API
            pass


async def http_error_handler(request: Request, exc: StarletteHTTPException):
    ctx = _ctx()
    if ctx is not None:
        ctx["error"] = str(exc.detail)
    return await http_exception_handler(request, exc)


async def validation_error_handler(request: Request, exc: RequestValidationError):
    ctx = _ctx()
    if ctx is not None:
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", [])[1:]) or "body"
        ctx["error"] = f"invalid input: {field} - {first.get('msg', '')}"
    return await request_validation_exception_handler(request, exc)


def install(app) -> None:
    setup_logging()
    app.middleware("http")(activity_middleware)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
