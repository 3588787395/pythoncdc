# -*- coding: utf-8 -*-
"""R21 锚点 02 —— 只有根因 A：BoolOp 链吞掉「前缀是 yield 语句」的 then 臂首块。

同层结构（块号沿用目标函数）：
    566: LOAD_FAST status … POP_JUMP_IF_NONE -> 726      (条件块，含 `status = yield …` 前缀)
    624: CALL YIELD_VALUE RESUME POP_TOP                  (then 臂首块 = **语句 + 嵌套 if**)
         LOAD_GLOBAL cgroupmode … POP_JUMP_IF_FALSE -> 730
    692/730/726: 三个 `return`
非首成员块守卫（region_analyzer.py:24186-24200）只查 STORE_*，看不到
`yield f()` 的 CALL…POP_TOP，于是 624 被并成 `and` 操作数：
产物 `if status is not None and cgroupmode == '1':` ⇒ 块 730 的 return 整块消失。
"""


class H(object):
    def then_arm_yield(self, user, user_id):
        status = yield user.spawner.poll()
        if status is not None:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
        return
