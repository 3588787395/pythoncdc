# Repro 11: async/await coroutine
# Pattern: async def with await expression
# Generates GET_AWAITABLE/SEND/YIELD_VALUE sequence
# Decompiler may mishandle coroutine protocol
import asyncio

async def fetch(url):
    await asyncio.sleep(0.01)
    return url
