"""Async multi-context ``with`` shapes.

Same anchor branch as pj_with_01 but on BEFORE_ASYNC_WITH paths (the anchor
line also accepts GET_AWAITABLE / SEND / YIELD_VALUE / RESUME).
"""


class ACtx:
    def __init__(self, tag):
        self.tag = tag

    async def __aenter__(self):
        return self.tag

    async def __aexit__(self, *exc):
        return False


async def pj_entry(a, b):
    """Zero-arg-callable entry: async two-item with."""
    async with ACtx(a) as first, ACtx(b) as second:
        out = (first, second)
    return out


async def pj_entry_await(a, b):
    """Zero-arg-callable entry: async with plus awaits inside the body."""
    async with ACtx(a) as x, ACtx(b) as y:
        left = await _one(x)
        right = await _one(y)
    return left, right


async def _one(v):
    return v


async def pj_entry_async_try(a):
    """Zero-arg-callable entry: async with inside try/finally."""
    try:
        async with ACtx(a) as x:
            return x
    finally:
        pass


async def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return await pj_entry(1, 2), await pj_entry_await(1, 2)

def main():
    return pj_entry(1, 2), pj_entry_await(1, 2)


if __name__ == "__main__":
    main()
