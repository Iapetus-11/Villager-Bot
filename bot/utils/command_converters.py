from typing import TypeVar, cast
import re
from dateutil.relativedelta import relativedelta


from discord.ext import commands


class DurationDelta(commands.Converter[relativedelta]):
    """Convert duration strings into dateutil.relativedelta.relativedelta objects. Taken from https://github.com/ClemBotProject/ClemBot"""

    DURATION_REGEX = re.compile(
        r"((?P<years>\d+?) ?(years|year|Y|y) ?)?"
        r"((?P<months>\d+?) ?(months|month|M) ?)?"
        r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
        r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|hr|H|h) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|min|m) ?)?"
        r"((?P<seconds>\d+?) ?(seconds|second|sec|S|s))?"
    )

    async def convert(self, ctx: commands.Context, duration: str) -> relativedelta:
        """
        Converts a `duration` string to a relativedelta objects.
        The converter supports the following symbols for each unit of time:
        - years: `Y`, `y`, `year`, `years`
        - months: `M`, `month`, `months`
        - weeks: `w`, `W`, `week`, `weeks`
        - days: `d`, `D`, `day`, `days`
        - hours: `H`, `h`, `hour`, `hours`
        - minutes: `m`, `min`, `minute`, `minutes`
        - seconds: `S`, `sec`, `s`, `second`, `seconds`
        The units need to be provided in descending order of magnitude.
        """

        match = self.DURATION_REGEX.fullmatch(duration)
        if not match:
            raise commands.ConversionError(f"`{duration}` is not a valid duration string.")

        duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}
        delta = relativedelta(**duration_dict)  # type: ignore

        # Add one second to the delta to account for passing second when we send it,
        # This fixes the embed being a second delayed
        delta.seconds += 1

        return cast(relativedelta, delta)
