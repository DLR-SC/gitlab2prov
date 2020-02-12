# Copyright (C) 2018 Quentin Pradet
# License: MIT
#
# github-gist: https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741

import asyncio
import time

from aiohttp import ClientSession

# Token bucket rate limited aiohttp.ClientSession
# https://en.wikipedia.org/wiki/Token_bucket


class Session(ClientSession):
    RATE = 10  # e. g. number of requests per second
    MAX_TOKENS = 10  # token cap

    def __init__(self, *args, rate=10, **kwargs):
        super().__init__(*args, **kwargs)

        self.RATE = self.MAX_TOKENS = rate
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        await self.wait_for_token()
        return super().get(*args, **kwargs)

    async def wait_for_token(self):
        while self.tokens <= 1:
            self.add_new_tokens()
            await asyncio.sleep(0.01)
        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.RATE
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now
