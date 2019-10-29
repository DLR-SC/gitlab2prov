# Token bucket rate limited aiohttp.ClientSession
# https://en.wikipedia.org/wiki/Token_bucket

import time
import asyncio
from aiohttp import ClientSession


class RateLimiter(ClientSession):
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
