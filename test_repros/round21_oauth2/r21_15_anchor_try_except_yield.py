# -*- coding: utf-8 -*-
"""R21 锚点 15 —— A 族形状外面套 try/except（已知陷阱：POP_TOP/PUSH_NULL 记账）。

Round 21 任务书点名的陷阱：try/except + with 处理器里 −9 常常是记账指令或
`__exit__` 清理尾巴。本复现把同族形状放进 try/except，验证
① 基线核上丢的仍是**语句块**（不是记账指令），
② R21-A 的间隙集合不含 PUSH_NULL/CALL_FUNCTION_EX/POP_EXCEPT 等，
   不会把异常清理尾巴误判成语句。
"""


class H(object):
    def try_except_yield(self, user, user_id):
        try:
            status = yield self.poll(user)
        except Exception as ex:
            self.log(ex)
            return
        if status is not None:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
        return
