from aiohttp import web


async def set_response_headers(request: web.Request, response: web.Response) -> None:
    """Set the response headers into the response."""

    response.headers.update(request["response_headers"])


ON_RESPONSE_PREPARE_SIGNALS: list = [set_response_headers]


async def clean_client(application: web.Application) -> None:
    """Clean the client."""

    await application["client"].close()


ON_CLEANUP_SIGNALS: list = [clean_client]

__all__ = ["ON_RESPONSE_PREPARE_SIGNALS", "ON_CLEANUP_SIGNALS"]
