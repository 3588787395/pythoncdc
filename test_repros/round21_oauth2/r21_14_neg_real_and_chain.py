# -*- coding: utf-8 -*-
"""R21 负对照 14 —— **真正的** and/or 短路链，协程语句只在 body 块里。

`if a is not None and b:` 的第二操作数块 = `LOAD_FAST b POP_JUMP_IF_FALSE`，
块内既无 STORE_* 也无 CALL…POP_TOP ⇒ 两半守卫都必须放行，链保持为 BoolOp。
基线核与候选核都必须 MATCH。
"""


class H(object):
    def real_and_chain(self, a, b, user):
        if a is not None and b:
            yield self.f(user)
            return
        return

    def real_or_chain(self, a, b, user):
        if a is None or not b:
            yield self.f(user)
            return
        return
