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

from discord.ext import commands

import config
from utilities import context, enums, exceptions


class ReminderRepeatTypeConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> enums.ReminderRepeatType:

        if enum := getattr(enums.ReminderRepeatType, argument.replace(' ', '_').upper(), None):
            return enum

        valid = [f"{repeat_type.name.replace('_', ' ').lower()}" for repeat_type in enums.ReminderRepeatType]
        raise exceptions.ArgumentError(f'Repeat type must be one of:\n{f"{config.NL}".join([f"- {v}" for v in valid])}')
