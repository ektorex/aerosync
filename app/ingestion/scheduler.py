import asyncio

class Scheduler:

    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback

    async def start(self):

        while True:

            await self.callback()

            await asyncio.sleep(self.interval)
