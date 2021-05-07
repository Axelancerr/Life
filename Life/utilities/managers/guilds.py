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

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from discord.ext import tasks

from utilities import objects

if TYPE_CHECKING:
    from bot import Life


__log__ = logging.getLogger('utilities.managers.guilds')


class GuildManager:

    def __init__(self, bot: Life) -> None:
        self.bot = bot

        self.default_config = objects.GuildConfig(bot=self.bot, data={})
        self.configs: dict[int, objects.GuildConfig] = {}

    async def load(self) -> None:

        configs = await self.bot.db.fetch('SELECT * FROM guilds')

        for config in configs:
            self.configs[config['id']] = objects.GuildConfig(bot=self.bot, data=config)

        __log__.info(f'[GUILD MANAGER] Loaded guild configs. [{len(configs)} guilds]')
        print(f'[GUILD MANAGER] Loaded guild configs. [{len(configs)} guilds]')

        await self.load_tags()

        self.update_database_task.start()

    async def load_tags(self) -> None:

        tags = await self.bot.db.fetch('SELECT * FROM tags')

        for tag in tags:
            guild_config = self.get_config(tag['guild_id'])
            tag = objects.Tag(bot=self.bot, guild_config=guild_config, data=tag)
            guild_config._tags[tag.name] = tag

        __log__.info(f'[TAG MANAGER] Loaded tags. [{len(tags)} tags]')
        print(f'[TAG MANAGER] Loaded tags. [{len(tags)} tags]')

    # Background task

    @tasks.loop(seconds=60)
    async def update_database_task(self) -> None:

        async with self.bot.db.acquire(timeout=300) as db:

            requires_updating = {guild_id: guild_config for guild_id, guild_config in self.configs.items() if len(guild_config._requires_db_update) >= 1}
            for guild_id, guild_config in requires_updating.items():

                query= ','.join(f'{editable.value} = ${index + 2}' for index, editable in enumerate(guild_config.requires_db_update))
                args = [getattr(guild_config, attribute.value) for attribute in guild_config.requires_db_update]
                await db.execute(f'UPDATE users SET {query} WHERE id = $1', guild_id, *args)

                guild_config.requires_db_update = set()

    # Config management

    async def create_config(self, guild_id: int) -> objects.GuildConfig:

        data = await self.bot.db.fetchrow('INSERT INTO guilds (id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.id RETURNING *', guild_id)

        guild_config = objects.GuildConfig(bot=self.bot, data=data)
        self.configs[guild_config.id] = guild_config

        __log__.info(f'[GUILD MANAGER] Created config for guild with id \'{guild_id}\'.')
        return guild_config

    def get_config(self, guild_id: int) -> objects.GuildConfig:
        return self.configs.get(guild_id, self.default_config)

    async def delete_config(self, guild_id: int) -> None:

        if not (config := self.get_config(guild_id)):
            return

        await config.delete()
