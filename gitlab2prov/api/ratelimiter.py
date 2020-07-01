# Copyright (C) 2018 Quentin Pradet
# License: MIT
#
# github-gist: https://gist.github.com/pquentin/5d8f5408cdad73e589d85ba509091741
"""
Wrapper for aiohttp.ClientSession that limits the number of calls the
Session can make per second.
"""

import asyncio
import time
from typing import Any

import aiohttp


class RateLimiter:
    """
    Rate limits an HTTP client that would make get() and post() calls.
    Calls are rate-limited by host.
    https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
    This class is not thread-safe.
    """
    RATE = 10
    MAX_TOKENS = 10

    def __init__(self, client: aiohttp.ClientSession, rate: int) -> None:
        self.RATE = self.MAX_TOKENS = rate

        self.client = client
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def close(self) -> None:
        """Close client session."""
        await self.client.close()

    async def get(self, *args: Any, **kwargs: Any) -> Any:
        """Perform GET request when token is available."""
        await self.wait_for_token()
        return self.client.get(*args, **kwargs)

    async def wait_for_token(self) -> None:
        """
        Wait and periodically wake up to check whether token is now
        available. If so, take a token from the token pool.
        """
        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.05)
        self.tokens -= 1

    def add_new_tokens(self) -> None:
        """Add tokens to the token pool."""
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.RATE
        if self.tokens + new_tokens >= 1:
            self.tokens = min(int(self.tokens + new_tokens), self.MAX_TOKENS)
            self.updated_at = now
