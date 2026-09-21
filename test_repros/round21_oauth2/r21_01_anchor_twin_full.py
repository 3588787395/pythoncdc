# -*- coding: utf-8 -*-
"""R21 锚点 01 —— 目标孪生 `OAuthCallbackHandler.post` 534..838 段的**完整同构克隆**。

真实形状（site-packages/fly/oauthenticator/oauth2.pyc，strict 尺子 orig=190 decomp=181）：

    if user.spawner:
        if user.spawn_pending:
            return
        status = yield user.spawner.poll()      # 块 566：赋值 + 条件跳转
        if status is not None:                  # 块 566 尾 POP_JUMP_IF_NONE -> 726
            yield self.spawn_single_user(user)  # 块 624：**前缀是 yield 语句**
            if cgroupmode == '1':               #   块 624 尾 POP_JUMP_IF_FALSE -> 730
                set_cgroup_config(user_id)
                return                          # 块 692
            return                              # 块 730
        return                                  # 块 726
    else:
        yield self.spawn_single_user(user)      # 块 734：**同样前缀 yield 语句**
        if cgroupmode == '1':                   #   块 734 尾 POP_JUMP_IF_FALSE -> 836
            set_cgroup_config(user_id)
            return                              # 块 802
        return                                  # 块 836

一个 `yield f()` 语句 = `LOAD_FAST/LOAD_METHOD/… CALL YIELD_VALUE RESUME POP_TOP`。
两处同层谓词都缺"协程弹栈间隙"这一半：
  A `region_analyzer._detect_boolop_conditional_chain` 非首成员块守卫（24186-24200）
    只查 STORE_*，漏了同函数起始块 24013-24035 的「CALL…POP_TOP」半边
    ⇒ 624 被当 BoolOp 操作数，`if status is not None and cgroupmode == '1':`（丢 730）。
  B `region_analyzer._check_elif_chain` 的 `_has_body_stmt`（18216-18243）已有
    「CALL 紧跟 POP_TOP」判据，但过滤表没排除 YIELD_VALUE
    ⇒ 734 被当纯 elif 条件块，前缀语句被推到 if/elif/else 链之后 ⇒ 被 3.11 死代码消除。
两半合计正好 −9。
"""


class OAuthCallbackHandler(object):
    def post(self):
        user = self.get_current_user()
        if user is None:
            user_id = yield self.authenticate()
            if user_id:
                user = self.user_from_username(user_id)
                self.set_login_cookie(user)
                if user.spawner:
                    if user.spawn_pending:
                        return
                    status = yield user.spawner.poll()
                    if status is not None:
                        yield self.spawn_single_user(user)
                        if self.cgroupmode == '1':
                            self.set_cgroup_config(user_id)
                            return
                        return
                    return
                else:
                    yield self.spawn_single_user(user)
                    if self.cgroupmode == '1':
                        self.set_cgroup_config(user_id)
                        return
                    return
            else:
                self.write('no user')
                return
        else:
            self.write('already logged in')
            return
