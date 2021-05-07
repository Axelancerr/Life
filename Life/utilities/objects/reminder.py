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

import aioscheduler.task
import discord
import pendulum
from pendulum import DateTime

from utilities import enums, objects, utils

if TYPE_CHECKING:
    from bot import Life


__log__ = logging.getLogger('utilities.objects.reminder')

REPEAT_TYPES = {
    1:  lambda dt: dt.add(minutes=30),
    2:  lambda dt: dt.add(hours=1),
    3:  lambda dt: dt.add(hours=2),
    4:  lambda dt: dt.add(hours=12),
    5:  lambda dt: dt.add(days=1),
    6:  lambda dt: dt.add(days=2),
    7:  lambda dt: dt.add(days=7),
    8:  lambda dt: dt.add(days=14),
    9:  lambda dt: dt.add(weeks=2),
    10: lambda dt: dt.add(months=1),
    11: lambda dt: dt.add(months=2),
    12: lambda dt: dt.add(months=6),
    13: lambda dt: dt.add(years=1),
    14: lambda dt: dt.add(years=2),
    15: lambda dt: dt.add(seconds=30)
}


class Reminder:

    __slots__ = '_bot', '_user_config', '_id', '_user_id', '_channel_id', '_created_at', '_content', '_jump_url', '_repeat_type', '_notified', '_datetime', '_task'

    def __init__(self, bot: Life, user_config: objects.user.UserConfig, data: dict) -> None:

        self._bot = bot
        self._user_config = user_config

        self._id: int = data.get('id')
        self._user_id: int = data.get('user_id')
        self._channel_id: int = data.get('channel_id')
        self._created_at: DateTime = pendulum.instance(data.get('created_at'), tz='UTC')
        self._content: str = data.get('content')
        self._jump_url: str = data.get('jump_url')
        self._repeat_type: enums.ReminderRepeatType = enums.ReminderRepeatType(value=data.get('repeat_type'))
        self._notified: bool = data.get('notified')
        self._datetime: DateTime = pendulum.instance(data.get('datetime'), tz='UTC')

        self._task: Optional[aioscheduler.task.Task] = None

    def __repr__(self) -> str:
        return f'<Reminder id=\'{self.id}\' channel_id=\'{self.channel_id}\' user_id=\'{self.user_id}\' datetime={self.datetime} notified={self.notified} done={self.done}>'

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
    def channel_id(self) -> int:
        return self._channel_id

    @property
    def created_at(self) -> DateTime:
        return self._created_at

    @property
    def content(self) -> str:
        return self._content

    @property
    def jump_url(self) -> str:
        return self._jump_url

    @property
    def repeat_type(self) -> enums.ReminderRepeatType:
        return self._repeat_type

    @property
    def notified(self) -> bool:
        return self._notified

    @property
    def datetime(self) -> DateTime:
        return self._datetime

    @property
    def task(self) -> aioscheduler.task.Task:
        return self._task

    #

    @property
    def done(self) -> bool:
        return pendulum.now(tz='UTC') > self.datetime

    # Misc

    async def delete(self) -> None:

        if not self.done:
            self.bot.scheduler.cancel(self.task)

        await self.bot.db.execute('DELETE FROM reminders WHERE id = $1', self.id)
        del self.user_config.reminders[self.id]

    # Handling

    def schedule(self) -> None:

        self._task = self.bot.scheduler.schedule(self.handle_notification(), when=self.datetime.naive())
        __log__.info(f'[REMINDER] Scheduled reminder with id \'{self.id}\' for \'{self.datetime}\'.')

    async def handle_notification(self) -> None:

        # TODO user user_configs user attribute here.

        user = self.bot.get_user(self.user_id)
        channel = self.bot.get_channel(self.channel_id)

        embed = discord.Embed(
                colour=self.user_config.colour,
                title='Reminder:',
                description=f'[`{utils.format_difference(datetime=self.created_at, suppress=[])} ago:`]({self.jump_url})\n\n{self.content}'
        )

        try:
            await channel.send(f'{user.mention if isinstance(user, discord.User) else f"<@{self.user_id}>"}', embed=embed)
        except (discord.Forbidden, AttributeError):
            try:
                await user.send(embed=embed)
            except (discord.Forbidden, AttributeError):
                __log__.warning(f'[REMINDER] Reminded with id \'{self.id}\' failed because channel or user no longer exist.')

        await self.set_notified()
        if self.repeat_type != enums.ReminderRepeatType.NEVER:
            await self.handle_repeat()

    async def handle_repeat(self) -> None:

        self._task = None

        await self.change_datetime(REPEAT_TYPES[self.repeat_type.value](self._datetime))
        await self.set_notified(False)

        self.schedule()

    # Config

    async def set_notified(self, notified: bool = True) -> None:

        data = await self.bot.db.fetchrow('UPDATE reminders SET notified = $1 WHERE id = $2 RETURNING notified', notified, self.id)
        self._notified = data['notified']

    async def change_datetime(self, datetime: DateTime) -> None:

        data = await self.bot.db.fetchrow('UPDATE reminders SET datetime = $1 WHERE id = $2 RETURNING datetime', datetime, self.id)
        self._datetime = pendulum.instance(data['datetime'], tz='UTC')

    async def change_content(self, content: str, *, jump_url: str = None) -> None:

        data = await self.bot.db.fetchrow('UPDATE reminders SET content = $1, jump_url = $2 WHERE id = $3 RETURNING content, jump_url', content, jump_url, self.id)
        self._content = data['content']
        self._jump_url = data['jump_url'] or self.jump_url

    async def change_repeat_type(self, repeat_type: enums.ReminderRepeatType) -> None:

        data = await self.bot.db.fetchrow('UPDATE reminders SET repeat_type = $1 WHERE id = $2 RETURNING repeat_type', repeat_type.value, self.id)
        self._repeat_type = enums.ReminderRepeatType(data['repeat_type'])
