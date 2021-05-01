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
from typing import Optional, TYPE_CHECKING

import discord
import pendulum
from pendulum import DateTime

from utilities import enums, objects

if TYPE_CHECKING:
    from bot import Life


__log__ = logging.getLogger('utilities.objects.guild')


class GuildConfig:

    __slots__ = '_bot', '_id', '_created_at', '_blacklisted', '_blacklisted_reason', '_colour', '_embed_size', '_prefixes', '_tags', '_requires_db_update'

    def __init__(self, bot: Life, data: dict) -> None:

        self._bot = bot

        self._id: int = data.get('id', 0)
        self._created_at: DateTime = pendulum.instance(created_at, tz='UTC') if (created_at := data.get('created_at')) else pendulum.now(tz='UTC')

        self._blacklisted: bool = data.get('blacklisted', False)
        self._blacklisted_reason: Optional[str] = data.get('blacklisted_reason')

        self._colour: discord.Colour = discord.Colour(int(data.get('colour', '0xF1C40F'), 16))
        self._embed_size: enums.EmbedSize = enums.EmbedSize(data.get('embed_size', 0))
        self._prefixes: list[str] = data.get('prefixes', [])

        self._tags: dict[str, objects.Tag] = {}

        self._requires_db_update: set = set()

    def __repr__(self) -> str:
        return f'<GuildConfig id=\'{self.id}\' blacklisted={self.blacklisted} colour=\'{self.colour}\' embed_size={self.embed_size}>'

    # Properties

    @property
    def bot(self) -> Life:
        return self._bot

    @property
    def id(self) -> int:
        return self._id

    @property
    def created_at(self) -> DateTime:
        return self._created_at

    @property
    def blacklisted(self) -> bool:
        return self._blacklisted

    @property
    def blacklisted_reason(self) -> str:
        return self._blacklisted_reason

    @property
    def colour(self) -> discord.Colour:
        return self._colour

    @property
    def embed_size(self) -> enums.EmbedSize:
        return self._embed_size

    @property
    def prefixes(self):
        return self._prefixes

    @property
    def tags(self):
        return self._tags

    # Misc

    async def delete(self) -> None:

        await self.bot.db.execute('DELETE FROM guilds WHERE id = $1', self.id)
        del self.bot.guild_manager.configs[self.id]

    # Config

    async def set_blacklisted(self, blacklisted: bool, *, reason: str = None) -> None:

        data = await self.bot.db.fetchrow(
                'UPDATE guilds SET blacklisted = $1, blacklisted_reason = $2 WHERE id = $3 RETURNING blacklisted, blacklisted_reason',
                blacklisted, reason, self.id
        )
        self._blacklisted = data['blacklisted']
        self._blacklisted_reason = data['blacklisted_reason']

    async def set_colour(self, colour: str = str(discord.Colour.gold())) -> None:

        data = await self.bot.db.fetchrow('UPDATE guilds SET colour = $1 WHERE id = $2', f'0x{colour.strip("#")}', self.id)
        self._colour = discord.Colour(int(data['colour'], 16))

    async def set_embed_size(self, embed_size: enums.EmbedSize = enums.EmbedSize.LARGE) -> None:

        data = await self.bot.db.fetchrow('UPDATE guilds SET embed_size = $1 WHERE id = $2 RETURNING embed_size', embed_size.value, self.id)
        self._embed_size = enums.EmbedSize(data['embed_size'])

    async def change_prefixes(self, prefix: str = None, *, operation: enums.Operation = enums.Operation.ADD) -> None:

        if operation == enums.Operation.ADD:
            data = await self.bot.db.fetchrow('UPDATE guilds SET prefixes = array_append(prefixes, $1) WHERE id = $2 RETURNING prefixes', prefix, self.id)
        elif operation == enums.Operation.REMOVE:
            data = await self.bot.db.fetchrow('UPDATE guilds SET prefixes = array_remove(prefixes, $1) WHERE id = $2 RETURNING prefixes', prefix, self.id)
        elif operation == enums.Operation.RESET:
            data = await self.bot.db.fetchrow('UPDATE guilds SET prefixes = $1 WHERE id = $2 RETURNING prefixes', [], self.id)
        else:
            raise TypeError(f'change_prefixes expected one of {enums.Operation.ADD, enums.Operation.REMOVE, enums.Operation.RESET}, got {operation!r}.')

        self._prefixes = data['prefixes']

    # Tags