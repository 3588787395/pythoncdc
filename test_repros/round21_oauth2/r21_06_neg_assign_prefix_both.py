# -*- coding: utf-8 -*-
"""R21 负对照 06 —— A/B 两族同结构，但前缀语句是**赋值** `v = self.f()`。

STORE_FAST 同时命中 24186-24200 的 `_has_store` 与 18218-18225 的 `_has_body_stmt`，
基线核与候选核都必须 MATCH（两族守卫的"已有那一半"不得被 R21-A 破坏）。
"""


class H(object):
    def assign_then_arm(self, user, user_id):
        status = yield self.poll(user)
        if status is not None:
            ret = self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
        return

    def assign_else_arm(self, user, user_id):
        if user.spawner:
            yield self.poll(user)
            return
        else:
            ret = self.spawn_single_user(user)
            if self.cgroupmode == '1':
                self.set_cgroup_config(user_id)
                return
            return
