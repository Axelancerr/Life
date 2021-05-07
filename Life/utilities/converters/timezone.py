#  Life
#  Copyright (C) 2020 Axel#3456
#
#  Life is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later version.
#
#  Life is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
#  PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License along with Life. If not, see https://www.gnu.org/licenses/.
#

from abc import ABC

import pendulum
import rapidfuzz
from discord.ext import commands
from pendulum.tz.timezone import Timezone

from utilities import context, exceptions


class TimezoneConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> Timezone:

        if argument not in pendulum.timezones:
            msg = '\n'.join(f'- `{match[0]}`' for index, match in rapidfuzz.process.extract(query=argument, choices=pendulum.timezones, processor=lambda s: s))
            raise exceptions.ArgumentError(f'That was not a recognised timezone. Maybe you meant one of these?\n{msg}')

        return pendulum.timezone(argument)
