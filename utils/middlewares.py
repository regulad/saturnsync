import datetime

from aiohttp import web

from utils.database import Document

RATELIMIT_PERIOD_LENGTH: datetime.timedelta = datetime.timedelta(minutes=2)
RATELIMIT_MAX_PER_PERIOD: int = 1


@web.middleware
async def initialize_response_headers(request: web.Request, handler):
    """Initializes the item response_headers, which is used by a signal."""

    request["response_headers"] = {}

    return await handler(request)


@web.middleware
async def real_ip_behind_proxy(request: web.Request, handler):
    """Changes the remote attribute of the request to the X-Real-IP, if present. If you don't use a proxy,
    you should get rid of this middleware. Also, you should use a proxy."""

    if request.headers.get("X-Real-IP") is not None:
        request = request.clone(remote=request.headers.get("X-Real-IP"))

    return await handler(request)


@web.middleware
async def identify(request: web.Request, handler):
    """Identifies the user. This should be a snowflake. For point of demonstration, this is the request's remote."""

    request["uid"] = request.remote

    return await handler(request)


@web.middleware
async def get_document(request: web.Request, handler):
    """Fetches the document for a user from their identity."""

    request["document"] = await Document.get_document(
        request.app["database"]["users"],
        {"_id": request["uid"]},
    )

    return await handler(request)


@web.middleware
async def rate_limiter(request: web.Request, handler):
    """Rate-limits a user, if necessary."""

    time_now: datetime.datetime = datetime.datetime.utcnow()

    # Update/get the retry-after
    if request["document"].get("ratelimit", {}).get("start", time_now) <= time_now:
        time_later: datetime.datetime = time_now + RATELIMIT_PERIOD_LENGTH
        await request["document"].update_db(
            {"$set": {"ratelimit.start": time_later, "ratelimit.count": 0}}
        )
    else:
        time_later: datetime.datetime = request["document"]["ratelimit"]["start"]
    await request["document"].update_db({"$inc": {"ratelimit.count": 1}})

    # The maximum amount of requests a user can make per-hour.
    request["response_headers"]["X-RateLimit-Limit"] = str(
        request["document"].get("ratelimit", {}).get("per", RATELIMIT_MAX_PER_PERIOD)
    )

    # The amount of rate-limits remaining.
    request["response_headers"]["X-RateLimit-Remaining"] = str(
        request["document"].get("ratelimit", {}).get("per", RATELIMIT_MAX_PER_PERIOD)
        - request["document"].get("ratelimit", {}).get("count", 0)
    )

    # When the next period comes.
    request["response_headers"]["X-RateLimit-Reset"] = str(
        (time_later - time_now).total_seconds()
    )

    if request["document"].get("ratelimit", {}).get("count", 0) > request[
        "document"
    ].get("ratelimit", {}).get("per", 90):
        raise web.HTTPTooManyRequests
    else:
        return await handler(request)


MIDDLEWARE_CHAIN: list = [
    initialize_response_headers,
    real_ip_behind_proxy,
    identify,
    get_document,
    rate_limiter,
]

__all__ = ["MIDDLEWARE_CHAIN"]
