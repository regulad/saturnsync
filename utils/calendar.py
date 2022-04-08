from asyncio import get_event_loop, AbstractEventLoop
from datetime import tzinfo

from ics import *
from ics.parse import ContentLine
from pytz import UTC
from saturnscrape import *
from tzlocal import get_localzone


async def make_calendar(client: SaturnLiveClient, school_id: str, student_id: int) -> Calendar:
    """Make an ICS calendar from a calendar on https://saturn.live."""

    calendar_days: list[CalendarDay] = await client.get_calendar(school_id)
    schedules: list[BellSchedule] = await client.get_schedules(student_id, include_chats=False)
    student: Student = await client.get_student(student_id)

    school_name: str = school_id.replace('-', ' ').title()

    if isinstance(student, FullStudent):
        school_name = student.school_title

    loop: AbstractEventLoop = get_event_loop()
    calendar: Calendar = await loop.run_in_executor(
        None,
        lambda: Calendar(creator=str(f"saturn-{school_id}-{student_id}"))
    )
    localzone: tzinfo = get_localzone()

    calendar.extra.extend(
        [
            ContentLine('X-WR-CALNAME', value=f"Saturn {school_name} Schedule"),
            ContentLine('X-WR-CALDESC', value=f"Saturn {school_name} Schedule"),
        ]
    )

    for day in calendar_days:
        if day.schedule and not day.is_canceled:
            bell_schedule: BellSchedule = next(filter(lambda x: x.id == day.schedule.id, schedules))

            all_day_event: Event = Event(name=bell_schedule.display_name, begin=day.date, end=day.date)
            all_day_event.make_all_day()
            calendar.events.add(all_day_event)

            for period in bell_schedule.periods:
                if period.instance:
                    def_course: DefinedCourse = period.instance
                    course: Course = def_course.course

                    class_event: Event = Event(
                        name=f"Period {period.name} - {def_course.nickname or course.name} - {def_course.room}",
                        begin=period.start_time.replace(
                            year=day.date.year, month=day.date.month, day=day.date.day, tzinfo=localzone
                        ).astimezone(UTC),
                        end=period.end_time.replace(
                            year=day.date.year, month=day.date.month, day=day.date.day, tzinfo=localzone
                        ).astimezone(UTC),
                        attendees=[
                            Attendee(common_name=student.name, email=student.email) for student in def_course.classmates
                        ],
                        description="Staff: " + ", ".join(map(lambda x: x.name, def_course.staff))
                    )

                    calendar.events.add(class_event)
                else:
                    calendar.events.add(
                        Event(
                            name=period.name,
                            begin=period.start_time.replace(
                                year=day.date.year, month=day.date.month, day=day.date.day, tzinfo=localzone
                            ).astimezone(UTC),
                            end=period.end_time.replace(
                                year=day.date.year, month=day.date.month, day=day.date.day, tzinfo=localzone
                            ).astimezone(UTC),
                        )
                    )

    return calendar


__all__ = ["make_calendar"]
