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

import discord
from discord.ext import commands

from utilities import context, exceptions


class PrefixConverter(commands.clean_content, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> str:

        argument = discord.utils.escape_markdown(await super().convert(ctx, argument))
        if not argument:
            raise commands.BadArgument

        if '`' in argument:
            raise exceptions.ArgumentError('Your prefix can not contain backtick characters.')
        if len(argument) > 15:
            raise exceptions.ArgumentError('Your prefix can not be more than 15 characters.')

        return argument
