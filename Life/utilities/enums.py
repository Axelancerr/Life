#  Lif
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

import enum


class Environment(enum.Enum):

    PROD = 'prod'
    DEV = 'dev'


class Operation(enum.Enum):

    SET = 'set'
    UPDATE = SET

    RESET = 'reset'

    ADD = 'add'
    PLUS = ADD

    MINUS = 'remove'
    REMOVE = MINUS


class Updateable(enum.Enum):

    COINS = 'coins'
    XP = 'xp'


class EmbedSize(enum.Enum):

    LARGE = 0
    MEDIUM = 1
    SMALL = 2


class ReminderRepeatType(enum.Enum):

    NEVER = 0

    EVERY_HALF_HOUR = 1
    EVERY_HOUR = 2
    EVERY_OTHER_HOUR = 3
    BI_HOURLY = EVERY_OTHER_HOUR

    EVERY_HALF_DAY = 4
    EVERY_DAY = 5
    EVERY_OTHER_DAY = 6
    BI_DAILY = EVERY_OTHER_DAY

    EVERY_WEEK = 7
    EVERY_OTHER_WEEK = 8
    EVERY_FORTNIGHT = EVERY_OTHER_WEEK
    BI_WEEKLY = EVERY_OTHER_WEEK

    EVERY_HALF_MONTH = 9
    EVERY_MONTH = 10
    EVERY_OTHER_MONTH = 11
    BI_MONTHLY = EVERY_OTHER_MONTH

    EVERY_HALF_YEAR = 12
    EVERY_YEAR = 13
    EVERY_OTHER_YEAR = 14
    BI_YEARLY = EVERY_OTHER_YEAR

    EVERY_30_SECONDS = 15
