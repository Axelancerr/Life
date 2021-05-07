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

import io
import logging
import math
import os
import pathlib
import random
from typing import Literal, TYPE_CHECKING, Union

import discord
import pendulum
from PIL import Image, ImageDraw, ImageFont
from colorthief import ColorThief
from discord.ext import tasks

from utilities import exceptions, objects, utils

if TYPE_CHECKING:
    from bot import Life


__log__ = logging.getLogger('utilities.managers.users')

IMAGES = {
    'SAI': {
        'level_cards': [
            pathlib.Path('./resources/SAI/level_cards/1.png'),
            pathlib.Path('./resources/SAI/level_cards/2.png'),
            pathlib.Path('./resources/SAI/level_cards/3.png'),
            pathlib.Path('./resources/SAI/level_cards/4.png'),
        ]
    }
}

ARIAL_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../resources/fonts/arial.ttf'))
KABEL_BLACK_FONT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../resources/fonts/kabel_black.otf'))


class UserManager:

    def __init__(self, bot: Life) -> None:
        self.bot = bot

        self.default_config = objects.UserConfig(bot=self.bot, data={})
        self.configs: dict[int, objects.UserConfig] = {}

    async def load(self) -> None:

        configs = await self.bot.db.fetch('SELECT * FROM users')

        for config in configs:
            self.configs[config['id']] = objects.UserConfig(bot=self.bot, data=config)

        __log__.info(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')
        print(f'[USER MANAGER] Loaded user configs. [{len(configs)} users]')

        await self.load_notifications()
        await self.load_reminders()
        await self.load_todos()

        self.update_database_task.start()

    async def load_notifications(self) -> None:

        notifications = await self.bot.db.fetch('SELECT * FROM notifications')

        for notification in notifications:
            user_config = self.get_config(notification['user_id'])
            user_config._notifications = objects.Notifications(bot=self.bot, user_config=user_config, data=notification)

    async def load_reminders(self) -> None:

        reminders = await self.bot.db.fetch('SELECT * FROM reminders')

        for reminder in reminders:
            user_config = self.get_config(reminder['user_id'])

            reminder = objects.Reminder(bot=self.bot, user_config=user_config, data=reminder)
            if not reminder.done:
                reminder.schedule()

            user_config._reminders[reminder.id] = reminder

        __log__.info(f'[USER MANAGER] Loaded reminders. [{len(reminders)} reminders]')
        print(f'[USER MANAGER] Loaded reminders. [{len(reminders)} reminders]')

    async def load_todos(self) -> None:

        todos = await self.bot.db.fetch('SELECT * FROM todos')

        for todo in todos:
            user_config = self.get_config(todo['user_id'])
            todo = objects.Todo(bot=self.bot, user_config=user_config, data=todo)
            user_config._todos[todo.id] = todo

        __log__.info(f'[USER MANAGER] Loaded todos. [{len(todos)} todos]')
        print(f'[USER MANAGER] Loaded todos. [{len(todos)} todos]')

    # Background task

    @tasks.loop(seconds=60)
    async def update_database_task(self) -> None:

        async with self.bot.db.acquire(timeout=300) as db:

            requires_updating = {user_id: user_config for user_id, user_config in self.configs.items() if len(user_config._requires_db_update) >= 1}
            for user_id, user_config in requires_updating.items():

                query= ','.join(f'{editable.value} = ${index + 2}' for index, editable in enumerate(user_config.requires_db_update))
                args = [getattr(user_config, attribute.value) for attribute in user_config.requires_db_update]
                await db.execute(f'UPDATE users SET {query} WHERE id = $1', user_id, *args)

                user_config.requires_db_update = set()

    # Config management

    async def create_config(self, user_id: int) -> objects.UserConfig:

        data = await self.bot.db.fetchrow('INSERT INTO users (id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.id RETURNING *', user_id)
        notifications = await self.bot.db.fetchrow('INSERT INTO notifications (user_id) values ($1) ON CONFLICT (id) DO UPDATE SET id = excluded.user_id RETURNING *', user_id)

        user_config = objects.UserConfig(bot=self.bot, data=data)
        user_config._notifications = objects.Notifications(bot=self.bot, user_config=user_config, data=notifications)

        self.configs[user_config.id] = user_config

        __log__.info(f'[USER MANAGER] Created config for user with id \'{user_config.id}\'.')
        return user_config

    def get_config(self, user_id: int) -> objects.UserConfig:
        return self.configs.get(user_id, self.default_config)

    async def delete_config(self, user_id: int) -> None:

        if not (config := self.get_config(user_id)):
            return

        await config.delete()

    # Ranking

    def leaderboard(self, *, guild_id: int = None, leaderboard_type: Literal['level', 'xp', 'coins']) -> list[objects.UserConfig]:

        if not guild_id:
            configs = filter(lambda user_config: self.bot.get_user(user_config.id) is not None and getattr(user_config, leaderboard_type) != 0, self.configs.values())

        else:
            if not (guild := self.bot.get_guild(guild_id)):
                raise ValueError(f'guild with id \'{guild_id}\' was not found.')
            configs = filter(lambda user_config: guild.get_member(user_config) is not None and getattr(user_config, leaderboard_type) != 0, self.configs.values())

        return sorted(configs, key=lambda user_config: getattr(user_config, leaderboard_type), reverse=True)

    def rank(self, user_id: int, *, guild_id: int = None) -> int:

        if not guild_id:
            configs = sorted(
                    filter(lambda user_config: self.bot.get_user(user_config.id) is not None and user_config.xp != 0, self.configs.values()),
                    key=lambda user_config: user_config.xp, reverse=True
            )

        else:

            if not (guild := self.bot.get_guild(guild_id)):
                raise ValueError(f'guild with id \'{guild_id}\' was not found.')

            configs = sorted(
                    filter(lambda user_config: guild.get_member(user_config.id) is not None and user_config.xp != 0, self.configs.values()),
                    key=lambda user_config: user_config.xp, reverse=True
            )

        try:
            return configs.index(self.get_config(user_id)) + 1
        except ValueError:
            raise exceptions.ArgumentError('That user does not have any XP yet, so they have not been ranked.')

    # Level image

    async def create_level_card(self, user_id: int, *, guild_id: int) -> discord.File:

        guild = self.bot.get_guild(guild_id)
        user = guild.get_member(user_id)
        user_config = self.get_config(user_id)

        avatar_bytes = io.BytesIO(await user.avatar_url_as(format='png', size=256).read())

        buffer = await self.bot.loop.run_in_executor(None, self.create_level_card_image, user, user_config, avatar_bytes)
        file = discord.File(fp=buffer, filename='level.png')

        buffer.close()
        avatar_bytes.close()

        return file

    def create_level_card_image(self, member: Union[discord.Member, discord.User], user_config: objects.UserConfig, avatar_bytes: io.BytesIO) -> io.BytesIO:

        buffer = io.BytesIO()
        card_image = random.choice(IMAGES['SAI']['level_cards'])

        with Image.open(card_image) as image:

            draw = ImageDraw.Draw(image)

            with Image.open(avatar_bytes) as avatar:

                avatar = avatar.resize((256, 256), resample=Image.LANCZOS) if avatar.size != (256, 256) else avatar
                image.paste(avatar, (22, 22), avatar.convert('RGBA'))

                colour = ColorThief(avatar_bytes).get_color(quality=1)

            # Username

            name_text = getattr(member, 'nick', None) or member.name
            name_fontsize = 56
            name_font = ImageFont.truetype(KABEL_BLACK_FONT, name_fontsize)

            while draw.textsize(name_text, font=name_font) > (690, 45):
                name_fontsize -= 1
                name_font = ImageFont.truetype(KABEL_BLACK_FONT, name_fontsize)

            draw.text((300, 22 - name_font.getoffset(name_text)[1]), name_text, font=name_font, fill=colour)

            # Level

            level_text = f'Level: {user_config.level}'
            level_font = ImageFont.truetype(KABEL_BLACK_FONT, 40)

            draw.text((300, 72 - level_font.getoffset(level_text)[1]), level_text, font=level_font, fill='#1F1E1C')

            # XP

            xp_text = f'XP: {user_config.xp} / {user_config.xp + user_config.next_level_xp}'
            xp_font = ImageFont.truetype(KABEL_BLACK_FONT, 40)

            draw.text((300, 112 - xp_font.getoffset(xp_text)[1]), xp_text, font=xp_font, fill='#1F1E1C')

            # XP BAR

            bar_len = 678
            outline = utils.darken_colour(*colour, 0.2)

            draw.rounded_rectangle(((300, 152), (300 + bar_len, 192)), radius=10, outline=outline, fill='#1F1E1C', width=5)

            if user_config.xp > 0:
                filled_len = int(round(bar_len * user_config.xp / float(user_config.xp + user_config.next_level_xp)))
                draw.rounded_rectangle(((300, 152), (300 + filled_len, 192)), radius=10, outline=outline, fill=colour, width=5)

            # Rank

            rank_text = f'#{self.rank(member.id)}'
            rank_font = ImageFont.truetype(KABEL_BLACK_FONT, 110)

            draw.text((300, 202 - rank_font.getoffset(rank_text)[1]), rank_text, font=rank_font, fill='#1F1E1C')

            #

            image.save(buffer, 'png')

        buffer.seek(0)
        return buffer

    # Timecard image

    async def create_timecard(self, *, guild_id: int) -> discord.File:

        guild = self.bot.get_guild(guild_id)

        user_configs = filter(
                lambda kv: guild.get_member(kv[0]) is not None and not kv[1].timezone_private and kv[1].timezone != pendulum.timezone('UTC'),
                sorted(self.bot.user_manager.configs.items(), key=lambda kv: kv[1].time.offset_hours)
        )
        timezone_avatars = {}

        # noinspection PyTypeChecker
        for user_config in dict(user_configs).values():

            avatar_bytes = io.BytesIO(await guild.get_member(user_config.id).avatar_url_as(format='png', size=256).read())
            timezone = user_config.time.format('HH:mm (ZZ)')

            if users := timezone_avatars.get(timezone, []):
                if len(users) > 36:
                    break
                timezone_avatars[timezone].append(avatar_bytes)
            else:
                timezone_avatars[timezone] = [avatar_bytes]

        if not timezone_avatars:
            raise exceptions.ArgumentError('There are no users with timezones set in this server.')

        buffer = await self.bot.loop.run_in_executor(None, self.create_timecard_image, timezone_avatars)
        file = discord.File(fp=buffer, filename='level.png')

        buffer.close()
        for avatar_bytes in timezone_avatars.values():
            [buffer.close() for buffer in avatar_bytes]

        return file

    @staticmethod
    def create_timecard_image(timezone_users: dict) -> io.BytesIO:

        buffer = io.BytesIO()
        width_x, height_y = (1600 * (len(timezone_users) if len(timezone_users) < 5 else 5)) + 100, (1800 * math.ceil(len(timezone_users) / 5)) + 100

        with Image.new(mode='RGBA', size=(width_x, height_y), color='#F1C30F') as image:

            draw = ImageDraw.Draw(im=image)
            font = ImageFont.truetype(font=ARIAL_FONT, size=120)

            x, y = 100, 100

            for timezone, avatars in timezone_users.items():

                draw.text(xy=(x, y), text=timezone, font=font, fill='#1B1A1C')
                user_x, user_y = x, y + 200

                for avatar_bytes in avatars:

                    with Image.open(fp=avatar_bytes) as avatar:
                        avatar = avatar.resize(size=(250, 250), resample=Image.LANCZOS)
                        image.paste(im=avatar, box=(user_x, user_y), mask=avatar.convert(mode='RGBA'))

                    if user_x < x + 1200:
                        user_x += 250
                    else:
                        user_y += 250
                        user_x = x

                if x > 6400:
                    y += 1800
                    x = 100
                else:
                    x += 1600

            image.save(fp=buffer, format='png')

        buffer.seek(0)
        return buffer
