# -*- coding: utf-8 -*-
"""R21 负对照 07 —— **真正的** elif 链：条件块全是纯测试块，语句只在 body 块里。

每个 elif 条件块 = `LOAD_FAST x POP_JUMP_IF_FALSE`，块内无 CALL…POP_TOP、无 STORE_*
⇒ `_has_body_stmt` 必须保持 False，链必须展平。基线核与候选核都必须 MATCH。
（Round 20 的教训：宽判据在小电池绿、在全量上净负。）
"""


class H(object):
    def pure_elif(self, a, b, c):
        if a:
            yield self.f1()
            return
        elif b:
            yield self.f2()
            return
        elif c:
            yield self.f3()
            return
        else:
            yield self.f4()
            return
