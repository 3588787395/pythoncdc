# -*- coding: utf-8 -*-
"""R21 锚点 03 —— 只有根因 B：`else:` 臂首块「前缀 yield 语句 + 嵌套 if」被当纯 elif 条件块。

目标块 734（else 臂）：
    LOAD_FAST self / LOAD_METHOD spawn_single_user / LOAD_FAST user
    CALL YIELD_VALUE RESUME POP_TOP        <- 语句（值被丢弃）
    LOAD_GLOBAL cgroupmode / LOAD_CONST '1' / COMPARE_OP / POP_JUMP_IF_FALSE -> 836
`_check_elif_chain` 的 `_has_body_stmt`（region_analyzer.py:18216-18243）本来就要挡这种块，
但它的 CALL→POP_TOP 逐字邻接判据看不见夹在中间的 YIELD_VALUE（RESUME 已被过滤），
于是 734 被吸收成 `elif cgroupmode == '1':`，前缀语句退到 if/elif/else 链之后；
链的三支全 return ⇒ 退到链后的语句被 CPython 3.11 死代码消除（−7）。
"""


class H(object):
    def else_arm_yield(self, user, user_id):
        if user.spawner:
            yield self.poll(user)
            return
        else:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
