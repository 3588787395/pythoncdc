# -*- coding: utf-8 -*-
"""R21 锚点 09 —— 两层嵌套的 A/B 同族形状（检验"自底向上归约 + 嵌套即抽象节点"不被破坏）。

内层再套一层 `yield f()` 前缀 + 条件跳转。若 R21-A 只是把某一层硬掰平，
第 2 层仍会丢；若它破坏了嵌套支持，第 1 层会连带塌掉。
"""


class H(object):
    def nested_two_levels(self, user, user_id):
        status = yield self.poll(user)
        if status is not None:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '1':
                yield self.set_cgroup_config(user_id)
                if self.cgx == '2':
                    self.tail(user_id)
                    return
                return
            return
        return
