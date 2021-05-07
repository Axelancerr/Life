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

import random

import discord
from discord.ext import commands

from bot import Life
from utilities import context, objects


class Economy(commands.Cog):

    def __init__(self, bot: Life) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:

        if message.author.bot:
            return

        if await self.bot.redis.exists(f'{message.author.id}_xp_gain') is True:
            return

        user_config = await self.bot.user_manager.get_or_create_config(message.author.id)

        xp = random.randint(10, 25)

        if xp >= user_config.next_level_xp:
            self.bot.dispatch('xp_level_up', user_config, message)

        await self.bot.user_manager.set_xp(message.author.id, xp=xp)
        await self.bot.redis.setex(name=f'{message.author.id}_xp_gain', time=60, value=None)

    @commands.Cog.listener()
    async def on_xp_level_up(self, user_config: objects.UserConfig, message: discord.Message) -> None:

        if not user_config.notifications.level_ups:
            return

        await message.reply(f'You are now level `{user_config.level}`!')

    #

    @commands.command(name='level', aliases=['xp', 'score', 'rank'])
    async def level(self, ctx: context.Context, *, member: discord.Member = None) -> None:
        """
        Display yours, or someone else's level / xp information.

        `member`: The member of which to get the level for. Can be their ID, Username, Nickname or @Mention. Defaults to you.
        """

        if not member:
            member = ctx.author

        async with ctx.typing():
            file = await self.bot.user_manager.create_level_card(member.id, guild_id=getattr(ctx.guild, 'id', None))
            await ctx.reply(file=file)


def setup(bot: Life) -> None:
    bot.add_cog(Economy(bot=bot))
