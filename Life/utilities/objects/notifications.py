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

from utilities import objects

if TYPE_CHECKING:
    from bot import Life


__log__ = logging.getLogger('utilities.objects.notifications')


class Notifications:

    __slots__ = 'bot', 'user_config', '_id', '_user_id', '_level_ups'

    def __init__(self, bot: Life, user_config: objects.UserConfig, data: dict) -> None:

        self.bot = bot
        self.user_config = user_config

        self._id: int = data.get('id', 0)
        self._user_id: int = data.get('user_id', 0)

        self._level_ups: bool = data.get('level_ups', False)

    def __repr__(self) -> str:
        return f'<Notifications id=\'{self.id}\' user_id=\'{self.user_id}\' level_ups={self.level_ups}>'

    #

    @property
    def id(self) -> int:
        return self._id

    @property
    def user_id(self) -> int:
        return self._user_id

    #

    @property
    def level_ups(self) -> bool:
        return self._level_ups
