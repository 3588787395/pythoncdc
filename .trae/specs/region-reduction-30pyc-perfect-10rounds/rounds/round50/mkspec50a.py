# -*- coding: utf-8 -*-
"""Emit the R50-A arm spec (hard-exit then arm + condition-head else_succ) for build2.py."""
import io
import json

HELPER = '''    def _r50a_exit_then_condition_head(self, header: BasicBlock,
                                       then_succ: BasicBlock,
                                       else_succ: BasicBlock) -> bool:
        """ 区域归约算法原则 1（块 = 前导语句 + 唯一终止符）+ 原则 2（每块唯一归属）：
        then 臂是「硬退出块」（return/raise 终结且无正常流后继）、else_succ 只由本
        header 进入、且 else_succ 自身是下一条语句的条件头时，else_succ 就是 after-if
        点 ⇒ merge=else_succ（else_blocks 为空），不得留给 elif 链兜底去猜 merge。

        失败模式（order_api 的 future_order / option_order 偏移 130 的
        `if order_ is None: return None`）：then 臂 174 以 RETURN_VALUE 硬退出，
        else_succ 178（`is_trade()` + POP_JUMP_FORWARD_IF_TRUE）的唯一前驱就是 130 ⇒
        上文 _else_has_external_pred 判据不触发；178 沿 ipdom 链最终抵达函数尾 return
        ⇒ _else_sink 被判为 True ⇒ 「then sink ∧ else 非 sink」分支整体跳过，merge 留空。
        于是 _build_elif_region 的链式 merge 兜底把 178 当 elif 条件头，并把 178 之后那条
        语句里【三元表达式】的两臂块（344=JUMP_FORWARD '买入'、348=LOAD_CONST '卖出'，
        已归属 TernaryRegion@206）错认成 elif body 与 final_else，取二者共同后继 350 作
        merge ⇒ 整条 `strategy_log.info(...format(...))` 语句失去归属者：三元漏成兄弟
        语句、其 LOAD_METHOD+CALL 被错绑为 upper(<ternary>)，strict seq_len 101→93、
        83→74。

        安全性：then 臂硬退出，故「if c: 退出」+后续语句 与「if c: 退出 else: 后续语句」
        编译为逐字相同的指令序列（then 臂不需要 JUMP_FORWARD 到 merge），判据只改变区域
        归属而不改变跳转语义。五条合取项全是同层结构事实：① then_succ 终结符属
        return/raise 族；② then_succ 无正常流后继（异常边除外）；③ else_succ 终结符属
        前向条件跳转/短路跳转族；④ else_succ 恰有两个条件后继；⑤ else_succ 的前驱非空
        且全部就是本 header（有外部前驱的场景由 _else_has_external_pred 分支负责，两条
        路径互斥）。
        """
        _r50a_then_last = then_succ.get_last_instruction()
        if (_r50a_then_last is None
                or _r50a_then_last.opname not in ('RETURN_VALUE', 'RETURN_CONST',
                                                  'RAISE_VARARGS', 'RERAISE')):
            return False
        _r50a_exc = getattr(then_succ, 'exception_successors', set()) or set()
        if [s for s in (then_succ.successors or []) if s not in _r50a_exc]:
            return False
        _r50a_else_last = else_succ.get_last_instruction()
        if (_r50a_else_last is None
                or _r50a_else_last.opname not in
                (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)):
            return False
        if len(else_succ.conditional_successors or []) != 2:
            return False
        _r50a_preds = list(else_succ.predecessors or [])
        return bool(_r50a_preds) and all(p is header for p in _r50a_preds)

'''

ANCHOR_A = '    def _compute_merge_from_jump_targets(self, header: BasicBlock,'
CALL = ('                # 区域归约算法原则 2（每块唯一归属）·R50-A：then 臂硬退出 +\n'
        '                # else_succ 是仅由本 header 进入的条件头 ⇒ else_succ 即 after-if 点。\n'
        '                if merge is None and self._r50a_exit_then_condition_head(\n'
        '                        block, then_succ, else_succ):\n'
        '                    merge = else_succ\n')
ANCHOR_B = ('                if merge is None:\n'
            '                    _then_br_role = self.get_block_role(then_succ)\n')

spec = {
    'file': 'core/cfg/region_analyzer.py',
    'edits': [
        {'anchor': ANCHOR_A, 'repl': HELPER + ANCHOR_A},
        {'anchor': ANCHOR_B, 'repl': CALL + ANCHOR_B},
    ],
}
OUT = r'D:\Temp\r50mine\spec_r50a.json'
io.open(OUT, 'w', encoding='utf-8', newline='\n').write(json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote', OUT)
