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

import collections
import sys

import discord
import humanize
import pkg_resources
import setproctitle
from discord.ext import commands

import config
import time
from bot import Life
from utilities import context, converters, exceptions


class Dev(commands.Cog):

    def __init__(self, bot: Life) -> None:
        self.bot = bot

    @commands.is_owner()
    @commands.group(name='dev', hidden=True, invoke_without_command=True)
    async def dev(self, ctx: context.Context) -> None:
        """
        Base command for bot developer commands.

        Displays a message with stats about the bot.
        """

        python_version = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
        discordpy_version = pkg_resources.get_distribution('discord.py').version
        platform = sys.platform
        process_name = setproctitle.getproctitle()
        process_id = self.bot.process.pid
        thread_count = self.bot.process.num_threads()

        description = [f'I am running on the python version **{python_version}** on the OS **{platform}** using the discord.py version **{discordpy_version}**. '
                       f'The process is running as **{process_name}** on PID **{process_id}** and is using **{thread_count}** threads.']

        if isinstance(self.bot, commands.AutoShardedBot):
            description.append(f'The bot is automatically sharded with **{self.bot.shard_count}** shard(s) and can see **{len(self.bot.guilds)}** guilds and '
                               f'**{len(self.bot.users)}** users.')
        else:
            description.append(f'The bot is not sharded and can see **{len(self.bot.guilds)}** guilds and **{len(self.bot.users)}** users.')

        with self.bot.process.oneshot():

            memory_info = self.bot.process.memory_full_info()
            physical_memory = humanize.naturalsize(memory_info.rss)
            virtual_memory = humanize.naturalsize(memory_info.vms)
            unique_memory = humanize.naturalsize(memory_info.uss)
            cpu_usage = self.bot.process.cpu_percent(interval=None)

            description.append(f'The process is using **{physical_memory}** of physical memory, **{virtual_memory}** of virtual memory and **{unique_memory}** of memory '
                               f'that is unique to the process. It is also using **{cpu_usage}%** of CPU.')

        embed = discord.Embed(title=f'{self.bot.user.name} bot information page.', colour=0xF5F5F5)
        embed.description = '\n\n'.join(description)

        await ctx.send(embed=embed)

    @commands.is_owner()
    @dev.command(name='cleanup', aliases=['clean'], hidden=True)
    async def dev_cleanup(self, ctx: context.Context, limit: int = 50) -> None:
        """
        Clean up the bots messages.

        `limit`: The amount of messages to check back through. Defaults to 50.
        """

        if ctx.channel.permissions_for(ctx.me).manage_messages:
            messages = await ctx.channel.purge(check=lambda message: message.author == ctx.me or message.content.startswith(config.PREFIX), bulk=True, limit=limit)
        else:
            messages = await ctx.channel.purge(check=lambda message: message.author == ctx.me, bulk=False, limit=limit)

        await ctx.send(f'Found and deleted `{len(messages)}` of my message(s) out of the last `{limit}` message(s).', delete_after=3)

    @commands.is_owner()
    @dev.command(name='guilds', hidden=True)
    async def dev_guilds(self, ctx: context.Context, guilds: int = 20) -> None:
        """
        Display a list of guilds the bot is in.

        `guilds`: The amount of guilds to show per page.
        """

        entries = []

        for guild in sorted(self.bot.guilds, reverse=True, key=lambda _guild: sum(bool(member.bot) for member in _guild.members) / len(_guild.members) * 100):

            total = len(guild.members)
            members = sum(not m.bot for m in guild.members)
            bots = sum(1 for m in guild.members if m.bot)
            percent_bots = f'{round((bots / total) * 100, 2)}%'

            entries.append(f'{guild.id:<19} |{total:<10}|{members:<10}|{bots:<10}|{percent_bots:10}|{guild.name}')

        header = 'Guild id            |Total     |Members   |Bots      |Percent   |Name\n'
        await ctx.paginate(entries=entries, per_page=guilds, header=header, codeblock=True)

    @commands.is_owner()
    @dev.command(name='socketstats', aliases=['ss'], hidden=True)
    async def dev_socket_stats(self, ctx: context.Context) -> None:
        """
        Displays a list of socket event counts since bot startup.
        """

        event_stats = collections.OrderedDict(sorted(self.bot.socket_stats.items(), key=lambda kv: kv[1], reverse=True))
        events_total = sum(event_stats.values())
        # noinspection PyUnresolvedReferences
        events_per_second = round(events_total / round(time.time() - self.bot.start_time))

        description = [f'```py\n{events_total} socket events observed at a rate of {events_per_second} per second.\n']

        for event, count in event_stats.items():
            description.append(f'{event:29} | {count}')

        description.append('```')

        embed = discord.Embed(title=f'{self.bot.user.name} socket stats.', colour=ctx.colour, description='\n'.join(description))
        await ctx.send(embed=embed)

    @dev.group(name='blacklist', aliases=['bl'], hidden=True, invoke_without_command=True)
    async def dev_blacklist(self, ctx: context.Context) -> None:
        """
        Base command for blacklisting.
        """

        await ctx.send(f'Choose a valid subcommand. Use `{config.PREFIX}help dev blacklist` for more information.')

    @dev_blacklist.group(name='users', aliases=['user', 'u'], hidden=True, invoke_without_command=True)
    async def dev_blacklist_users(self, ctx: context.Context) -> None:
        """
        Display a list of blacklisted users.
        """

        blacklisted = [user_config for user_config in self.bot.user_manager.configs.values() if user_config.blacklisted is True]
        if not blacklisted:
            raise exceptions.ArgumentError('There are no blacklisted users.')

        entries = [f'{user_config.id:<19} | {user_config.blacklisted_reason}' for user_config in blacklisted]
        header = 'User id             | Reason\n'
        await ctx.paginate(entries=entries, per_page=15, header=header, codeblock=True)

    @dev_blacklist_users.command(name='add', hidden=True)
    async def dev_blacklist_users_add(self, ctx: context.Context, user: converters.UserConverter, *, reason: str = 'No reason') -> None:
        """
        Blacklist a user.

        `user`: The user to add to the blacklist.
        `reason`: Reason why the user is being blacklisted.
        """

        if reason == 'No reason':
            reason = f'{user.name} - No reason'

        user_config = self.bot.user_manager.get_config(user.id)
        if user_config.blacklisted is True:
            raise exceptions.ArgumentError('That user is already blacklisted.')

        await self.bot.user_manager.set_blacklisted(user.id, reason=reason)
        await ctx.send(f'Blacklisted user `{user.id}` with reason:\n\n`{reason}`')

    @dev_blacklist_users.command(name='remove', hidden=True)
    async def dev_blacklist_users_remove(self, ctx: context.Context, user: converters.UserConverter) -> None:
        """
        Unblacklist a user.

        `user`: The user to remove from the blacklist.
        """

        user_config = self.bot.user_manager.get_config(user.id)
        if user_config.blacklisted is False:
            raise exceptions.ArgumentError('That user is not blacklisted.')

        await self.bot.user_manager.set_blacklisted(user.id, blacklisted=False)
        await ctx.send(f'Unblacklisted user `{user.id}`.')

    @dev_blacklist.group(name='guilds', aliases=['guild', 'g'], hidden=True, invoke_without_command=True)
    async def dev_blacklist_guilds(self, ctx: context.Context) -> None:
        """
        Display a list of blacklisted guilds.
        """

        blacklisted = [guild_config for guild_config in self.bot.guild_manager.configs.values() if guild_config.blacklisted is True]
        if not blacklisted:
            raise exceptions.ArgumentError('There are no blacklisted guilds.')

        entries = [f'{guild_config.id:<19} | {guild_config.blacklisted_reason}' for guild_config in blacklisted]
        header = 'Guild id            | Reason\n'
        await ctx.paginate(entries=entries, per_page=10, header=header, codeblock=True)

    @dev_blacklist_guilds.command(name='add', hidden=True)
    async def dev_blacklist_guilds_add(self, ctx: context.Context, guild_id: int, *, reason: str = 'No reason') -> None:
        """
        Blacklist a guild.

        `guild`: The guild to add to the blacklist.
        `reason`: Reason why the guild is being blacklisted.
        """

        if 17 > guild_id > 20:
            raise exceptions.ArgumentError('That is not a valid guild id.')

        if (guild := self.bot.get_guild(guild_id)) and reason == 'No reason':
            reason = f'{guild.name} - No reason'
            await guild.leave()

        guild_config = self.bot.guild_manager.get_config(guild_id)
        if guild_config.blacklisted is True:
            raise exceptions.ArgumentError('The guild is already blacklisted.')

        await self.bot.guild_manager.set_blacklisted(guild_id, reason=reason)
        await ctx.send(f'Blacklisted guild `{guild_id}` with reason:\n\n`{reason}`')

    @dev_blacklist_guilds.command(name='remove', hidden=True)
    async def dev_blacklist_guilds_remove(self, ctx: context.Context, guild_id: int) -> None:
        """
        Unblacklist a guild.

        `guild`: The guild to remove from the blacklist.
        """

        if 17 > guild_id > 20:
            raise exceptions.ArgumentError('That is not a valid guild id.')

        guild_config = self.bot.guild_manager.get_config(guild_id)
        if guild_config.blacklisted is False:
            raise exceptions.ArgumentError('That guild is not blacklisted.')

        await self.bot.guild_manager.set_blacklisted(guild_id, blacklisted=False)
        await ctx.send(f'Unblacklisted guild `{guild_id}`.')


def setup(bot: Life) -> None:
    bot.add_cog(Dev(bot=bot))
