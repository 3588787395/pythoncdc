# -*- coding: utf-8 -*-
"""R21 锚点 16 —— then 臂**不终止**（有真实共享 merge 块）的同族形状。

    status = yield self.poll(user)
    if status is not None:
        yield self.spawn(user)          <- 前缀 yield 语句 + 嵌套 if
        if self.mode == '1':
            self.cfg(user)
    self.finish(user)                   <- 真正的 merge 块
与锚点 02/09 的区别：三支都不 return，merge 块非空。用来检查 R21-A 只在
"块内含值丢弃语句"这一条同层判据上起作用，不会把带真实 merge 的链拆坏。
"""


class H(object):
    def yield_prefix_with_real_merge(self, user, user_id):
        status = yield self.poll(user)
        if status is not None:
            yield self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
        self.finish(user)
        return
