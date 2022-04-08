"""
Regulad's aiohttp-mongodb-base
https://github.com/regulad/aiohttp-mongodb-base

If you want to run the webserver with an external provisioning/management system like Gunicorn,
run the awaitable create_app.
"""

import logging
from os import environ
from typing import Mapping

from aiohttp import web
from jwt import decode
from motor.motor_asyncio import AsyncIOMotorClient
from saturnscrape import SaturnLiveClient

from routes import ROUTES
from utils.middlewares import *
from utils.signals import *

CONFIGURATION_PROVIDER: Mapping[str, str] = environ
CONFIGURATION_KEY_PREFIX: str = "SATURN"


# This could be a JSON or YAML file if you want to to be.


async def create_app():
    """Create an app and configure it."""

    # Create the app
    app = web.Application(middlewares=MIDDLEWARE_CHAIN)

    # Config
    app["database_connection"] = AsyncIOMotorClient(
        CONFIGURATION_PROVIDER.get(f"{CONFIGURATION_KEY_PREFIX}_URI", "mongodb://mongo")
    )
    app["database"] = app["database_connection"][
        CONFIGURATION_PROVIDER.get(
            f"{CONFIGURATION_KEY_PREFIX}_DB", CONFIGURATION_KEY_PREFIX
        )
    ]

    # Token management
    given_token: str = CONFIGURATION_PROVIDER[f"{CONFIGURATION_KEY_PREFIX}_TOKEN"]
    decoded_token: dict = decode(given_token, options={'verify_signature': False}, algorithms=["HS256"])
    maybe_token: dict | None = await app["database"]["token"].find_one({})

    if maybe_token:
        decoded_maybe_token: dict = decode(maybe_token["token"], options={'verify_signature': False},
                                           algorithms=["HS256"])
        if decoded_maybe_token["exp"] > decoded_token["exp"]:
            given_token: str = maybe_token["token"]
        else:
            await app["database"]["token"].delete_one({"_id": maybe_token["_id"]})

    # Register client
    app["client"] = SaturnLiveClient(given_token, CONFIGURATION_PROVIDER[f"{CONFIGURATION_KEY_PREFIX}_REFRESH_TOKEN"])

    async def update_token(token: str):
        await app["database"]["token"].delete_many("{}")
        await app["database"]["token"].insert_one({"token": token})

    app["client"].on_token_change = update_token

    # Routes
    app.add_routes(ROUTES)

    # Signals
    app.on_response_prepare.extend(ON_RESPONSE_PREPARE_SIGNALS)

    app.on_cleanup.extend(ON_CLEANUP_SIGNALS)

    # Off we go!
    return app


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    )

    port = int(CONFIGURATION_PROVIDER.get(f"{CONFIGURATION_KEY_PREFIX}_PORT", "8081"))
    host = CONFIGURATION_PROVIDER.get(f"{CONFIGURATION_KEY_PREFIX}_HOST", "0.0.0.0")

    web.run_app(create_app(), host=host, port=port)
