import aiohttp
import asyncio

class AsyncAPIClient:

    async def fetch(self, session, url):

        async with session.get(url) as response:
            return await response.json()

    async def fetch_all(self, urls):

        async with aiohttp.ClientSession() as session:

            tasks = [
                self.fetch(session, url)
                for url in urls
            ]

            return await asyncio.gather(*tasks)
