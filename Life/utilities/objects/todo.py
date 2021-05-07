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

import pendulum
from pendulum import DateTime

from utilities import objects

if TYPE_CHECKING:
    from bot import Life


__log__ = logging.getLogger('utilities.objects.todo')


class Todo:

    __slots__ = '_bot', '_user_config', '_id', '_user_id', '_created_at', '_content', '_jump_url'

    def __init__(self, bot: Life, user_config: objects.UserConfig, data: dict) -> None:

        self._bot = bot
        self._user_config = user_config

        self._id: int = data.get('id')
        self._user_id: int = data.get('user_id')
        self._created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self._content: str = data.get('content')
        self._jump_url: Optional[str] = data.get('jump_url')

    def __repr__(self) -> str:
        return f'<Todo id=\'{self.id}\' user_id=\'{self.user_id}\'>'

    # Properties

    @property
    def bot(self) -> Life:
        return self._bot

    @property
    def user_config(self) -> objects.UserConfig:
        return self._user_config

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def created_at(self) -> DateTime:
        return self._created_at

    @property
    def content(self) -> str:
        return self._content

    @property
    def jump_url(self) -> Optional[str]:
        return self._jump_url

    # Misc

    async def delete(self) -> None:

        await self.bot.db.execute('DELETE FROM todos WHERE id = $1', self.id)
        del self.user_config._todos[self.id]

    # Config

    async def change_content(self, content: str, *, jump_url: str = None) -> None:

        data = await self.bot.db.fetchrow('UPDATE todos SET content = $1, jump_url = $2 WHERE id = $3 RETURNING content, jump_url', content, jump_url, self.id)
        self._content = data['content']
        self._jump_url = data['jump_url'] or self.jump_url
