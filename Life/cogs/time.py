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

import discord
import pendulum
import pendulum.tz.zoneinfo.exceptions
import rapidfuzz
from discord.ext import commands

import config
from bot import Life
from utilities import context, converters, exceptions, utils


class Time(commands.Cog):

    def __init__(self, bot: Life) -> None:
        self.bot = bot

    @commands.command(name='times')
    async def times(self, ctx: context.Context) -> None:

        user_configs = filter(
                lambda kv: ctx.guild.get_member(kv[0]) is not None and not kv[1].timezone_private and kv[1].timezone != pendulum.timezone('UTC'),
                sorted(self.bot.user_manager.configs.items(), key=lambda kv: kv[1].time.offset_hours)
        )
        timezone_users = {}

        # noinspection PyTypeChecker
        for user_config in dict(user_configs).values():

            timezone = user_config.time.format('HH:mm (ZZ)')
            member = ctx.guild.get_member(user_config.id)

            if timezone_users.get(timezone, []):
                timezone_users[timezone].append(f'{member} - {user_config.timezone.name}')
            else:
                timezone_users[timezone] = [f'{member} - {user_config.timezone.name}']

        if not timezone_users:
            raise exceptions.ArgumentError('There are no users with timezones set in this server.')

        entries = [f'`{timezone}:`\n{config.NL.join(members)}\n' for timezone, members in timezone_users.items()]
        await ctx.paginate_embed(entries=entries, per_page=5, title=f'Timezones in `{ctx.guild}:`\n\n')

    @commands.command(name='timezones', aliases=['tzs'])
    async def _timezones(self, ctx: context.Context) -> None:
        """
        Displays a list of timezones that can be used with the bot.
        """

        await ctx.paginate_embed(
                entries=pendulum.timezones, per_page=20,
                title='Available timezones:', header='Click [here](https://skeletonclique.mrrandom.xyz/timezones) to view a list of timezones.\n\n'
        )

    @commands.command(name='timecard', aliases=['tc'])
    async def timecard(self, ctx: context.Context) -> None:
        """
        Creates an image with the timezones of all the servers members.
        """

        async with ctx.typing():
            file = await self.bot.user_manager.create_timecard(guild_id=ctx.guild.id)
            await ctx.send(file=file)

    #

    @commands.group(name='timezone', aliases=['time'], invoke_without_command=True)
    async def _timezone(self, ctx: context.Context, *, timezone: str = None) -> None:
        """
        Displays the time of the member or timezone provided.

        `timezone`: The timezone or members Name, Nickname, ID, or @Mention that you want to get.
        """

        if not timezone:
            member = ctx.author
            timezone = ctx.user_config.timezone

        else:

            try:
                timezone = pendulum.timezone(timezone)
                member = ctx.author

            except pendulum.tz.zoneinfo.exceptions.InvalidTimezone:

                try:
                    member = await commands.MemberConverter().convert(ctx=ctx, argument=timezone)
                except commands.BadArgument:
                    msg = '\n'.join(f'- `{match[0]}`' for match in rapidfuzz.process.extract(query=timezone, choices=pendulum.timezones, processor=lambda s: s))
                    raise exceptions.ArgumentError(f'I did not recognise that timezone or member. Maybe you meant one of these?\n{msg}')
                else:
                    user_config = self.bot.user_manager.get_config(member.id)
                    if user_config.timezone_private is True and member.id != ctx.author.id:
                        raise exceptions.ArgumentError('That users timezone is private.')
                    timezone = user_config.timezone

        datetime = utils.format_datetime(datetime=pendulum.now(tz=timezone))
        embed = discord.Embed(colour=ctx.colour, title=f'Time in {timezone.name}{f" ({member})" if member else ""}:', description=f'```py\n{datetime}\n```')
        await ctx.send(embed=embed)

    @_timezone.command(name='set')
    async def _timezone_set(self, ctx: context.Context, *, timezone: converters.TimezoneConverter) -> None:
        """
        Sets your timezone.

        `timezone`: The timezone to use. See `l-timezones` for a list of timezones.
        """

        await ctx.user_config.set_timezone(timezone.name)
        await ctx.send(f'Your timezone has been set to `{ctx.user_config.timezone.name}`.')

    @_timezone.command(name='reset', aliases=['default'])
    async def _timezone_reset(self, ctx: context.Context) -> None:
        """
        Sets your timezone back to the default (UTC).
        """

        await ctx.user_config.set_timezone('UTC')
        await ctx.send(f'Your timezone has been reset back to `{ctx.user_config.timezone.name}`.')

    @_timezone.command(name='private')
    async def _timezone_private(self, ctx: context.Context) -> None:
        """
        Sets your timezone to be private.
        """

        if ctx.user_config.timezone_private is True:
            raise exceptions.ArgumentError('Your timezone is already private.')

        await ctx.user_config.set_timezone(private=True)
        await ctx.send('Your timezone is now private.')

    @_timezone.command(name='public')
    async def _timezone_public(self, ctx: context.Context) -> None:
        """
        Sets your timezone to be public.
        """

        if ctx.user_config.timezone_private is False:
            raise exceptions.ArgumentError('Your timezone is already public.')

        await ctx.user_config.set_timezone(private=False)
        await ctx.send('Your timezone is now public.')

    #

    @commands.group(name='reminders', aliases=['remind', 'reminder', 'remindme'], invoke_without_command=True)
    async def reminders(self, ctx: context.Context, *, reminder: converters.DatetimeConverter) -> None:
        """
        Schedule a reminder for the given time.

        `reminder`: The content of reminder, should include some form of date or time such as `tomorrow`, `in 12h` or `1st january 2020`.
        """

        entries = {index: (datetime_phrase, datetime) for index, (datetime_phrase, datetime) in enumerate(reminder['found'].items())}
        if len(entries) != 1:
            choice = await ctx.paginate_choice(
                     entries=[f'`{index + 1}.` **{phrase}**\n`{utils.format_datetime(datetime=datetime)}`' for index, (phrase, datetime) in entries.items()],
                     per_page=5, title='Multiple times/dates were detected in your query, please select the one you would like to be reminded at (type the number):\n\n'
            )
            result = entries[choice]
        else:
            result = entries[0]

        content = await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder['argument'], max_characters=1800)

        reminder = await ctx.user_config.create_reminder(channel_id=ctx.channel.id, datetime=result[1], content=content, jump_url=ctx.message.jump_url)
        datetime = utils.format_datetime(datetime=reminder.datetime, seconds=True)
        datetime_difference = utils.format_difference(datetime=reminder.datetime, suppress=[])

        await ctx.send(f'Created a reminder with ID `{reminder.id}` for `{datetime}`, `{datetime_difference}` from now.')

    @reminders.command(name='delete')
    async def reminders_delete(self, ctx: context.Context, *, reminder_ids: str) -> None:
        """
        Delete reminders with the given id's.

        `reminder_ids`: A list of reminders id's to delete, separated by spaces.
        """

        reminders_to_delete = []

        for reminder_id in reminder_ids.split(' '):

            try:
                reminder_id = int(reminder_id)
            except ValueError:
                raise exceptions.ArgumentError(f'`{reminder_id}` is not a valid reminder id.')

            if not (reminder := ctx.user_config.get_reminder(reminder_id)):
                raise exceptions.ArgumentError(f'You do not have a reminder with the id `{reminder_id}`.')
            if reminder in reminders_to_delete:
                raise exceptions.ArgumentError(f'You provided the id `{reminder_id}` more than once.')

            reminders_to_delete.append(reminder)

        for reminder in reminders_to_delete:
            await reminder.delete()

        s = 's' if len(reminders_to_delete) > 1 else ''
        await ctx.send(f'Deleted `{len(reminders_to_delete)}` reminder{s} with id{s} {", ".join(f"`{reminder.id}`" for reminder in reminders_to_delete)}.')

    @reminders.command(name='info')
    async def reminders_info(self, ctx: context.Context, reminder_id: int) -> None:
        """
        Display information about the reminder with the given id.
        """

        if not (reminder := ctx.user_config.get_reminder(reminder_id)):
            raise exceptions.ArgumentError('You do not have a reminder with that id.')

        difference = utils.format_difference(datetime=reminder.datetime, suppress=[])

        embed = discord.Embed(
                colour=ctx.colour, title=f'Reminder `{reminder.id}:`',
                description=f'[`{"In " if reminder.done is False else ""}{difference}{" ago" if reminder.done else ""}:`]({reminder.jump_url})\n' \
                            f'`Created:` {utils.format_datetime(datetime=reminder.created_at, seconds=True)}\n' \
                            f'`Scheduled for:` {utils.format_datetime(datetime=reminder.datetime, seconds=True)}\n'
                            f'`Repeat type:` {reminder.repeat_type.name.replace("_", " ").lower().title()}\n' \
                            f'`Done:` {reminder.done}\n\n' \
                            f'`Content:`\n {await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder.content, max_characters=1800)}\n'
        )

        await ctx.send(embed=embed)

    @reminders.command(name='list')
    async def reminders_list(self, ctx: context.Context) -> None:
        """
        Display a list of your active reminders.
        """

        if not (reminders := [reminder for reminder in ctx.user_config.reminders.values() if not reminder.done]):
            raise exceptions.ArgumentError('You do not have any active reminders.')

        entries = [
            f'`{reminder.id}:` [`In {utils.format_difference(datetime=reminder.datetime, suppress=[])}`]({reminder.jump_url})\n'
            f'`When:` {utils.format_datetime(datetime=reminder.datetime, seconds=True)}\n'
            f'`Content:` {await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder.content, max_characters=100)}\n'
            for reminder in sorted(reminders, key=lambda reminder: reminder.datetime)
        ]

        await ctx.paginate_embed(entries=entries, per_page=5, title=f'Active reminders for `{ctx.author}:`\n\n')

    @reminders.command(name='all')
    async def reminders_all(self, ctx: context.Context) -> None:
        """
        Display a list of all your reminders.
        """

        if not ctx.user_config.reminders:
            raise exceptions.ArgumentError('You do not have any reminders.')

        entries = [
            f'`{reminder.id}:` [`{"In " if reminder.done is False else ""}{utils.format_difference(datetime=reminder.datetime, suppress=[])}{" ago" if reminder.done else ""}`]' \
            f'({reminder.jump_url})\n'
            f'`When:` {utils.format_datetime(datetime=reminder.datetime, seconds=True)}\n'
            f'`Content:` {await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder.content, max_characters=100)}\n'
            f'`Done:` {reminder.done}\n'
            for reminder in sorted(ctx.user_config.reminders.values(), key=lambda reminder: reminder.datetime)
        ]

        await ctx.paginate_embed(entries=entries, per_page=5, title=f'All reminders for `{ctx.author}:`\n\n')

    @reminders.command(name='edit')
    async def reminders_edit(self, ctx: context.Context, reminder_id: int, *, content: str) -> None:
        """
        Edit a reminders content.

        `reminder_id`: The id of the reminder to edit.
        `content`: The content to edit the reminder with.
        """

        if not (reminder := ctx.user_config.get_reminder(reminder_id)):
            raise exceptions.ArgumentError('You do not have a reminder with that id.')

        content = await utils.safe_text(mystbin_client=self.bot.mystbin, text=content, max_characters=1800)
        await reminder.change_content(content, jump_url=ctx.message.jump_url)

        await ctx.send(f'Edited content of reminder with id `{reminder.id}`.')

    @reminders.group(name='repeat')
    async def reminder_repeat(self, ctx: context.Context, reminder_id: int, *, repeat_type: converters.ReminderRepeatTypeConverter) -> None:
        """
        Edit a reminders repeat type.

        `reminder_id`: The id of the reminder to edit.
        `content`: The repeat type to set on the reminder.
        """

        if not (reminder := ctx.user_config.get_reminder(reminder_id)):
            raise exceptions.ArgumentError('You do not have a reminder with that id.')

        await reminder.change_repeat_type(repeat_type)
        await ctx.send(f'Edited repeat type of reminder with id `{reminder.id}`.')


def setup(bot: Life) -> None:
    bot.add_cog(Time(bot=bot))
