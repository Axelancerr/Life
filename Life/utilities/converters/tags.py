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

from utilities import context, exceptions


class TagNameConverter(commands.clean_content, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> str:
        self.escape_markdown = True

        if not (argument := (await super().convert(ctx=ctx, argument=argument)).strip()):
            raise commands.BadArgument

        if argument.split(' ')[0] in (names := ctx.bot.get_command('tag').all_commands.keys()):
            raise exceptions.ArgumentError(f'Tag names can not start with a tag subcommand name. ({", ".join([f"`{name}`" for name in names])})')
        if len(argument) < 3 or len(argument) > 50:
            raise exceptions.ArgumentError('Tag names must be between 3 and 50 characters long.')

        return argument


class TagContentConverter(commands.clean_content, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> str:

        if not (argument := (await super().convert(ctx=ctx, argument=argument)).strip()):
            raise commands.BadArgument

        if len(argument) > 1500:
            raise exceptions.ArgumentError('Tag content can not be more than 1500 characters long.')

        return argument
