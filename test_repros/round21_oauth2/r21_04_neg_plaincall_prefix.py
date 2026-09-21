# -*- coding: utf-8 -*-
"""R21 负对照 04 —— B 族同结构，但 else 臂前缀是**普通调用** `self.s()`（无 yield）。

`_check_elif_chain` 已有的 `_has_body_stmt` 判据（region_analyzer.py:18216-18243）
对 `CALL` 紧跟 `POP_TOP` 的普通调用语句在基线核上就成立 ⇒ 不会被吸收成 elif。
基线核与候选核都必须 MATCH：R21-A 补的是 YIELD_VALUE 间隙，不得改变这一半的结论。
"""


class H(object):
    def plain_call_else(self, user, user_id):
        if user.spawner:
            self.poll(user)
            return
        else:
            self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
