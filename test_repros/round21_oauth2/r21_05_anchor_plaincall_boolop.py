# -*- coding: utf-8 -*-
"""R21 锚点 05 —— A 族但**不含协程**：then 臂首块前缀是普通调用语句。

非首成员块守卫（region_analyzer.py:24186-24200）只查 STORE_*，完全没有同函数起始块
（24013-24035）那半截「CALL 紧跟 POP_TOP」判据 ⇒ 普通调用语句块同样会被并成
BoolOp `and` 操作数。本复现用来证明：
  * 根因是"同层判据缺半"，不是"协程特例"；
  * R21-A 的两段补全里，缺半补全部分是独立收益（与 YIELD_VALUE 间隙无关）。
（若基线核实测为 MATCH，则本项按实测记为负对照，不得凭注释断言。）
"""


class H(object):
    def plain_call_then_arm(self, user, user_id):
        status = self.poll(user)
        if status is not None:
            self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
        return
