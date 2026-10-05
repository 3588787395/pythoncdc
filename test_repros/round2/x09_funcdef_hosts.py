"""x09: FunctionDef/AsyncFunctionDef as statements in deep hosts."""
def def_in_if():
    if 1:
        for i in range(1):
            def inner(v):
                return v + i
            r = inner(1)
    return r


def def_in_try():
    try:
        with _A():
            def inner2(v):
                if v:
                    for k in range(v):
                        while k:
                            k -= 1
                return k
    finally:
        F = 1
    return inner2(2)


class AHost:
    async def a1(self):
        async with _A() as a:
            if a:
                for i in range(2):
                    await self.a2(i)

    async def a2(self, v):
        async for i in _AIT():
            if i:
                acc = [x async for x in _AIT()]
                return i

    def sync_use(self):
        return (self.a1, self.a2)
