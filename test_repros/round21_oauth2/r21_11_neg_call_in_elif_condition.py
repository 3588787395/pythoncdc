# -*- coding: utf-8 -*-
"""R21 负对照 11 —— **条件块里含 CALL，但值被 COMPARE_OP 消费（无 POP_TOP）**。

`self.f(user) == '1'` 的块 = `… CALL … COMPARE_OP … POP_JUMP_IF_FALSE`：
CALL 之后的下一条有意义指令是 COMPARE_OP，不在 R21-A 的间隙集合
（YIELD_VALUE / RESUME）里 ⇒ 扫描立即停止，`_has_body_stmt` 保持 False，
elif 链照旧展平、and 链照旧合并。这条是防"看见 CALL 就算语句"这一自然错误改法的反例。

第二个方法给 A 族同位置（then 臂首块）的同一反例：块内含 CALL 但值进 COMPARE_OP。

（原计划用 `if (yield self.g(x)):` 作反例，实测该形状在本核上产物丢外层括号
⇒ `if yield self.g(x):` SyntaxError ⇒ 重编译 ERROR，无法进电池；
该括号丢失是与 R21-A 无关的另一处发射缺陷，记录在 ANALYSIS.md「未收口」。）
"""


class H(object):
    def neg_call_in_elif_condition(self, user):
        if user.a:
            self.s(user)
            return
        elif self.f(user) == '1':
            self.t(user)
            return
        else:
            return

    def neg_call_in_nested_condition(self, user):
        status = self.poll(user)
        if status is not None:
            self.spawn(user)
            if self.g(user) == '2':
                self.cfg(user)
                return
            return
        return
