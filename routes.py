from asyncio import get_running_loop

from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest
from ics import Calendar
from saturnscrape import Student

from saturnscrape.utils import make_calendar, make_contact
from vobject.base import Component

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


@ROUTES.get("/{student_id}.vcf")
async def get_contact_endpoint(request: web.Request):
    if request.match_info["student_id"] == "me":
        raise HTTPBadRequest(reason="You cannot access me")
    else:
        student: Student = await request.app["client"].get_student(request.match_info["student_id"])
        contact: Component = await get_running_loop().run_in_executor(None, lambda: make_contact(student))
        return web.Response(
            text=await get_running_loop().run_in_executor(None, lambda: contact.serialize()),
            content_type="text/vcard",
        )


__all__ = ["ROUTES"]
