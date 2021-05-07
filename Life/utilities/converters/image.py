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

import yarl
from discord.ext import commands

from utilities import context, utils


class ImageConverter(commands.Converter, ABC):

    async def convert(self, ctx: context.Context, argument: str) -> str:

        try:
            member = await commands.MemberConverter().convert(ctx=ctx, argument=str(argument))
        except commands.BadArgument:
            pass
        else:
            await ctx.send(f'Editing the avatar of `{member}`. If this is a mistake please specify the user/image you would like to edit before any extra arguments.')
            return utils.avatar(person=member)

        if (check := yarl.URL(argument)) and check.scheme and check.host:
            return argument

        try:
            emoji = await commands.EmojiConverter().convert(ctx=ctx, argument=str(argument))
        except commands.EmojiNotFound:
            pass
        else:
            return str(emoji.url)

        try:
            partial_emoji = await commands.PartialEmojiConverter().convert(ctx=ctx, argument=str(argument))
        except commands.PartialEmojiConversionFailure:
            pass
        else:
            return str(partial_emoji.url)

        url = f'https://twemoji.maxcdn.com/v/latest/72x72/{ord(argument[0]):x}.png'
        async with ctx.bot.session.get(url) as response:
            if response.status == 200:
                return url

        raise commands.ConversionError
