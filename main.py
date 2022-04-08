import os
from asyncio import get_event_loop, AbstractEventLoop, run
from typing import cast

from ics import *
from saturnscrape import *


async def make_calendar(client: SaturnLiveClient, school_id: str, student_id: int) -> Calendar:
    """Make an ICS calendar from a calendar on https://saturn.live."""
    loop: AbstractEventLoop = get_event_loop()
    calendar: Calendar = await loop.run_in_executor(
        None,
        lambda: Calendar(creator=str(f"saturn-{school_id}-{student_id}"))
    )

    calendar_days: list[CalendarDay] = await client.get_calendar(school_id)
    schedules: list[BellSchedule] = await client.get_schedules(student_id, include_chats=False)

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
                        begin=period.start_time.replace(year=day.date.year, month=day.date.month, day=day.date.day),
                        end=period.end_time.replace(year=day.date.year, month=day.date.month, day=day.date.day),
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
                            begin=period.start_time.replace(year=day.date.year, month=day.date.month, day=day.date.day),
                            end=period.end_time.replace(year=day.date.year, month=day.date.month, day=day.date.day),
                        )
                    )

    return calendar


if __name__ == "__main__":
    async def runnable():
        client: SaturnLiveClient = SaturnLiveClient(os.environ["SATURN_TOKEN"], os.environ["SATURN_REFRESH_TOKEN"])
        student: Student = await client.get_student("me")
        full_student: FullStudent = cast(FullStudent, student)
        calendar: Calendar = await make_calendar(client, full_student.school_id, full_student.id)
        with open("calendar.ics", "w") as f:
            f.writelines(calendar)


    run(runnable())
