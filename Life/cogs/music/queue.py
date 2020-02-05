import asyncio
import collections
import random


class Queue:

    def __init__(self, bot):

        self.bot = bot
        self.loop = asyncio.get_event_loop()
        self.getters = collections.deque()
        self.putters = collections.deque()
        self.unfinished_tasks = 0
        self.finished = asyncio.locks.Event(loop=self.loop)
        self.finished.set()

        self.queue_list = []

    @staticmethod
    def wakeup_next(waiters):
        while waiters:
            waiter = waiters.popleft()
            if not waiter.done():
                waiter.set_result(None)
                break

    def task_done(self):

        if self.unfinished_tasks <= 0:
            raise ValueError('task_done() called too many times')
        self.unfinished_tasks -= 1
        if self.unfinished_tasks == 0:
            self.finished.set()

    def empty(self):

        if not self.queue_list:
            return True
        return False

    def size(self):
        return len(self.queue_list)

    def clear(self):
        self.queue_list.clear()

    def reverse(self):
        self.queue_list.reverse()

    def shuffle(self):
        random.shuffle(self.queue_list)

    async def put(self, item):

        self.bot.dispatch("queue_add")
        return self.queue_list.append(item)

    async def put_pos(self, item, pos):

        self.bot.dispatch("queue_add")
        return self.queue_list.insert(pos, item)

    async def get(self):

        while self.empty():
            getter = self.loop.create_future()
            self.getters.append(getter)
            try:
                await getter
            except:
                getter.cancel()
                try:
                    self.getters.remove(getter)
                except ValueError:
                    pass
                if not self.empty() and not getter.cancelled():
                    self.wakeup_next(self.getters)
                raise
        self.wakeup_next(self.putters)

        item = self.queue_list.pop(0)
        return item

    async def get_pos(self, pos):

        while self.empty():
            getter = self.loop.create_future()
            self.getters.append(getter)
            try:
                await getter
            except:
                getter.cancel()
                try:
                    self.getters.remove(getter)
                except ValueError:
                    pass
                if not self.empty() and not getter.cancelled():
                    self.wakeup_next(self.getters)
                raise
        self.wakeup_next(self.putters)

        item = self.queue_list.pop(pos)
        return item
