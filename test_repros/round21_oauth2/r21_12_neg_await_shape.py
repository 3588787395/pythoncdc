# -*- coding: utf-8 -*-
"""R21 负对照 12 —— `await f()` 语句（async def）形状。

CPython 3.11 的 await 展开是
`CALL GET_AWAITABLE LOAD_CONST None SEND YIELD_VALUE JUMP_BACKWARD_NO_INTERRUPT POP_TOP`，
CALL 之后紧跟 GET_AWAITABLE（不在 R21-A 的间隙集合里）⇒ 补全不得命中，
两核结论必须相同。（同时给出证据：目标协程走的是 `yield`，不是 `await`。）
"""


class H(object):
    async def await_else(self, user, user_id):
        if user.spawner:
            await self.poll(user)
            return
        else:
            await self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
