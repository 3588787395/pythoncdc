# async function with await
import asyncio
async def test():
    results = await asyncio.gather(task1(), task2())
    return results
