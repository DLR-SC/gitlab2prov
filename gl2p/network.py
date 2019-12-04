# standard lib imports
import time
import asyncio

# third party imports
from aiohttp import ClientSession

# local imports
from gl2p.config import CONFIG


# Token bucket rate limited aiohttp.ClientSession
# https://en.wikipedia.org/wiki/Token_bucket

class RateLimitedClientSession(ClientSession):
    RATE = 10  # e.g. number of requests per second
    MAX_TOKENS = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        await self.wait_for_token()
        return super().get(*args, **kwargs)

    async def wait_for_token(self):
        while self.tokens <= 1:
            self.add_new_tokens()
            await asyncio.sleep(1)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.RATE
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now


class RateLimitedAsyncRequestHandler:

    def get_batch(self, urls):
        # Split batch into chunks, perform requests for all chunks
        # Avoids answer-request mapping slowdown for big batch size
        res = []
        chunk_size = 250  # chunk size
        for batch in (urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)):
            res.extend(asyncio.run(self._fetch(batch)))
        return res

    async def _fetch(self, urls):
        # NOTE: Send authentification header with each request
        # TODO: header as call parameter
        auth = {"Private-Token": CONFIG["GITLAB"]["token"]}
        async with RateLimitedClientSession(headers=auth) as client:
            tasks = [
                    asyncio.ensure_future(self._fetch_one(client, url))
                    for url in urls
                    ]
            return await asyncio.gather(*tasks)

    async def _fetch_one(self, client, url):
        async with await client.get(url) as resp:
            resp = await resp.json()
            return resp
