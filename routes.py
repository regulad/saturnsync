from asyncio import get_running_loop

from aiohttp import web
from ics import Calendar

from saturnscrape.utils import make_calendar

ROUTES: web.RouteTableDef = web.RouteTableDef()


@ROUTES.get("/{school_id}/{student_id}.ics")
async def get_calendar_endpoint(request: web.Request):
    school_id: str = request.match_info["school_id"]
    student_id: int = request.match_info["student_id"]
    calendar: Calendar = await make_calendar(request.app["client"], school_id, student_id)
    return web.Response(
        text=await get_running_loop().run_in_executor(None, lambda: str(calendar)),
        content_type="text/calendar",
    )


__all__ = ["ROUTES"]
