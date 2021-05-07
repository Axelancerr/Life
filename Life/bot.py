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
import logging
import time
from typing import Optional, Union

import aiohttp
import aioscheduler
import aredis
import asyncpg
import discord
import ksoftapi
import mystbin
import psutil
import slate
import spotify
from discord.ext import commands

import config
from utilities import context, help, managers  # skipcq: PYL-W0622

__log__ = logging.getLogger(__name__)


class Life(commands.AutoShardedBot):

    def __init__(self) -> None:
        super().__init__(
                command_prefix=self.get_prefix, help_command=help.HelpCommand(), owner_ids=config.OWNER_IDS, intents=discord.Intents.all(),
                activity=discord.Activity(type=discord.ActivityType.playing, name='the game of life'), max_messages=10000,
                allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)
        )

        self.text_permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True,
                                                    external_emojis=True)
        self.voice_permissions = discord.Permissions(read_messages=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, add_reactions=True,
                                                     external_emojis=True, connect=True, speak=True, use_voice_activation=True)

        self.session = aiohttp.ClientSession()
        self.start_time = time.time()
        self.process = psutil.Process()
        self.socket_stats = collections.Counter()

        self.DM_WEBHOOK = discord.Webhook.from_url(adapter=discord.AsyncWebhookAdapter(self.session), url=config.DM_WEBHOOK_URL)
        self.LOGGING_WEBHOOK = discord.Webhook.from_url(adapter=discord.AsyncWebhookAdapter(self.session), url=config.LOGGING_WEBHOOK_URL)
        self.ERROR_WEBHOOK = discord.Webhook.from_url(adapter=discord.AsyncWebhookAdapter(self.session), url=config.ERROR_WEBHOOK_URL)

        self.first_ready: bool = True

        self.db: Optional[asyncpg.Pool] = None
        self.redis: Optional[aredis.StrictRedis] = None

        self.mystbin: mystbin.Client = mystbin.Client()
        self.ksoft: Optional[ksoftapi.Client] = ksoftapi.Client(config.KSOFT_TOKEN)
        self.slate: Optional[slate.Client] = slate.Client(bot=self, session=self.session)
        self.spotify: Optional[spotify.Client] = spotify.Client(client_id=config.SPOTIFY_CLIENT_ID, client_secret=config.SPOTIFY_CLIENT_SECRET)
        self.spotify_http: Optional[spotify.HTTPClient] = spotify.HTTPClient(client_id=config.SPOTIFY_CLIENT_ID, client_secret=config.SPOTIFY_CLIENT_SECRET)
        self.scheduler: aioscheduler.Manager = aioscheduler.Manager(2)

        self.user_manager: managers.UserManager = managers.UserManager(bot=self)
        self.guild_manager: managers.GuildManager = managers.GuildManager(bot=self)

    async def get_context(self, message: discord.Message, *, cls=context.Context) -> context.Context:
        return await super().get_context(message, cls=cls)

    async def is_owner(self, user: Union[discord.User, discord.Member]) -> bool:
        return user.id in config.OWNER_IDS

    async def get_prefix(self, message: discord.Message) -> list[str]:

        if not message.guild:
            return commands.when_mentioned_or(config.PREFIX, 'I-', '')(self, message)

        guild_config = self.guild_manager.get_config(message.guild.id)
        return commands.when_mentioned_or(config.PREFIX, 'I-', *guild_config.prefixes)(self, message)

    async def start(self, *args, **kwargs) -> None:

        try:
            __log__.debug('[POSTGRESQL] Attempting connection.')
            db = await asyncpg.create_pool(**config.POSTGRESQL, max_inactive_connection_lifetime=0)
        except Exception as e:
            __log__.critical(f'[POSTGRESQL] Error while connecting.\n{e}\n')
            print(f'\n[POSTGRESQL] Error while connecting: {e}')
            raise ConnectionError
        else:
            __log__.info('[POSTGRESQL] Successful connection.')
            print('\n[POSTGRESQL] Successful connection.')
            self.db = db

        try:
            __log__.debug('[REDIS] Attempting connection')
            redis = aredis.StrictRedis(**config.REDIS)
            await redis.set('connected', 0)
        except (aredis.ConnectionError, aredis.ResponseError) as e:
            __log__.critical(f'[REDIS] Error while connecting.\n{e}\n')
            print(f'[REDIS] Error while connecting: {e}')
            raise ConnectionError()
        else:
            __log__.info('[REDIS] Successful connection.')
            print(f'[REDIS] Successful connection to Redis DB number \'{config.REDIS["db"]}\'. \n')
            self.redis = redis

        for extension in config.EXTENSIONS:
            try:
                self.load_extension(extension)
                __log__.info(f'[EXTENSIONS] Loaded - {extension}')
                print(f'[EXTENSIONS] Loaded - {extension}')
            except commands.ExtensionNotFound:
                __log__.warning(f'[EXTENSIONS] Extension not found - {extension}')
                print(f'\n[EXTENSIONS] Extension not found - {extension}\n')
            except commands.NoEntryPointError:
                __log__.warning(f'[EXTENSIONS] No entry point - {extension}')
                print(f'\n[EXTENSIONS] No entry point - {extension}\n')
            except commands.ExtensionFailed as error:
                __log__.warning(f'[EXTENSIONS] Failed - {extension} - Reason: {error}')
                print(f'\n[EXTENSIONS] Failed - {extension} - Reason: {error}\n')

        print('')
        await super().start(*args, **kwargs)

    async def close(self) -> None:

        __log__.info('[BOT] Closing aiohttp client sessions.')
        print('\n[CS] Closing aiohttp client sessions.')
        await self.mystbin.close()
        await self.ksoft.close()
        await self.session.close()
        await self.spotify.close()
        await self.spotify_http.close()

        __log__.info('[BOT] Closing bot down.')
        print('[BOT] Closing bot down.')

        __log__.info('[BOT] Closing database connection.')
        print('[DB] Closing database connection.')
        await self.db.close()

        __log__.info('[BOT] Bot has shutdown.')
        print('\nBye bye!')
        await super().close()

    #

    async def on_ready(self) -> None:

        if self.first_ready is False:
            return
        self.first_ready = False

        self.add_check(self.command_check)
        self.scheduler.start()

        await self.user_manager.load()
        await self.guild_manager.load()

        for cog in self.cogs.values():
            if hasattr(cog, 'load'):
                await cog.load()

    async def command_check(self, ctx: context.Context) -> bool:

        if ctx.user_config.blacklisted is True and ctx.command.qualified_name not in {'help', 'support'}:
            raise commands.CheckFailure(f'You are blacklisted from using this bot with the reason:\n\n`{ctx.user_config.blacklisted_reason}`')
        if ctx.guild_config.blacklisted is True and ctx.command.qualified_name not in {'help', 'support'}:
            raise commands.CheckFailure(f'This guild is blacklisted from using this bot with the reason:\n\n`{ctx.guild_config.blacklisted_reason}`')

        needed_permissions = {permission: value for permission, value in self.text_permissions if value is True}
        current_permissions = dict(ctx.me.permissions_in(ctx.channel))
        if not ctx.guild:
            current_permissions['read_messages'] = True

        if ctx.command.cog and ctx.command.cog in {self.get_cog('Music')}:  # skipcq: PTC-W0048
            if (channel := getattr(ctx.author.voice, 'channel', None)) is not None:
                needed_permissions = {permission: value for permission, value in self.voice_permissions if value is True}
                current_permissions.update({permission: value for permission, value in ctx.me.permissions_in(channel) if value is True})

        if missing := [permissions for permissions, value in needed_permissions.items() if current_permissions[permissions] != value]:
            raise commands.BotMissingPermissions(missing)

        return True
