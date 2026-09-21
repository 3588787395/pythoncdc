# -*- coding: utf-8 -*-
"""R21 锚点 08 —— elif 链的**每一支 body** 里都嵌 A 族结构（协程前缀 + 嵌套 if）。

同层同结构必须同结论：`if … elif … else` 展开出的每个 body 臂首块都带
`yield f()` 前缀，A 族缺半判据会同时命中多支 ⇒ 一次反编译里出现多处
`and` 合并。候选核必须三支全部还原。
"""


class H(object):
    def elif_bodies_yield(self, a, b, user, user_id):
        if a:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
        elif b:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '2':
                self.set_cgroup_config(user_id)
                return
            return
        else:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '3':
                self.set_cgroup_config(user_id)
                return
            return
