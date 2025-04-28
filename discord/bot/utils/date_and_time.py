from datetime import date, timedelta
import re


def parse_timedelta(duration: str) -> timedelta | None:
    """
    Converts a `duration` string to a relativedelta objects.
    - weeks: `w`, `W`, `week`, `weeks`
    - days: `d`, `D`, `day`, `days`
    - hours: `H`, `h`, `hour`, `hours`
    - minutes: `m`, `min`, `minute`, `minutes`
    - seconds: `S`, `sec`, `s`, `second`, `seconds`
    The units need to be provided in descending order of magnitude.

    CREDIT: This code was taken and modified from https://github.com/ClemBotProject/ClemBot
    """

    DURATION_REGEX = re.compile(
        r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
        r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|hr|H|h) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|min|M|m) ?)?",
    )

    match = DURATION_REGEX.fullmatch(duration)
    if not match:
        return None

    duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}

    return timedelta(**duration_dict)


def get_timedelta_granularity(delta: timedelta, granularity: int) -> list[str]:
    def _get_timedelta_granularity():
        if delta.days >= 365:
            yield "year"

        if delta.days % 365 >= 31:
            yield "month"

        if delta.days % 30 >= 7:
            yield "week"

        if delta.days % 7 >= 1:
            yield "day"

        if delta.seconds >= 3600:
            yield "hour"

        if delta.seconds % 3600 >= 60:
            yield "minute"

        if delta.seconds % 60 >= 1:
            yield "second"

    return list(_get_timedelta_granularity())[:granularity]


def today_within_date_range(date_range: tuple[tuple[int, int], tuple[int, int]]) -> bool:
    start, end = date_range

    today = date.today()
    today_tuple = (today.month, today.day)

    return start <= today_tuple <= end
