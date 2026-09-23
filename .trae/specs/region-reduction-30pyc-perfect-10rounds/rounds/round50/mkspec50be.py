# -*- coding: utf-8 -*-
"""Emit R50-B and R50-E arm specs for build2.py."""
import io
import json

B_HELPER_DOC = ''

# ---------------- R50-B: chain-merge candidates must not be ternary-owned ---------
B_ANCHOR = '            if _chain_merge_candidates:\n'
B_REPL = '''            # 区域归约算法原则 2（每块唯一归属）+ 原则 4（父区域按入口块引用子区域）：
            # 已被某个三元（表达式）区域认领、且其入口块不在本链结构内的块，不得作链的
            # merge 候选。失败模式（order_api 的 future_order / option_order 偏移 130）：
            # `if order_ is None: return None` 的 then 臂硬退出、merge 留空，链式兜底把
            # 下一条语句的条件头 178 当作 elif 条件，并把 178 之后那条语句里三元区域的
            # 两臂块（344=JUMP_FORWARD、348=LOAD_CONST，均属 TernaryRegion@206）认作
            # elif body 与 final_else，取二者共同后继 350 作 merge ⇒ 整条
            # `strategy_log.info(...format(...))` 语句失去归属者，三元漏成兄弟语句。
            _r50b_struct = {block} | set(then_blocks) | set(else_blocks)
            for _r50b_c in elif_info.get("conditions", []):
                _r50b_struct.add(_r50b_c)
            for _r50b_body in elif_info.get("bodies", []):
                _r50b_struct.update(_r50b_body)
            _r50b_struct.update(elif_info.get("final_else", []))
            _r50b_owned = set()
            for _r50b_tr in self._filter_regions(ternary_regions or [], TernaryRegion):
                if _r50b_tr.entry in _r50b_struct:
                    continue
                _r50b_owned.update(getattr(_r50b_tr, 'blocks', None) or ())
            _chain_merge_candidates -= _r50b_owned
            if _chain_merge_candidates:
'''
spec_b = {'file': 'core/cfg/region_analyzer.py',
          'edits': [{'anchor': B_ANCHOR, 'repl': B_REPL}]}

# ---------------- R50-E: narrowed rebind at the earlier sink site -----------------
E_HELPER = '''    def _r50e_exit_then_head_into_ternary(self, header: BasicBlock,
                                          then_succ: BasicBlock,
                                          else_succ: BasicBlock,
                                          ternary_regions) -> bool:
        """ 区域归约算法原则 1 + 原则 2：then 臂是硬退出块（return/raise 终结且无正常流
        后继）、else_succ 只由本 header 进入且自身是条件头、并且 else_succ 的某个后继正是
        某三元区域的入口块时，else_succ 是 after-if 点 ⇒ merge=else_succ。

        第三个合取项把判据限定在「后续语句以嵌套三元表达式开头」这一确证失败的形状上：
        此时若 merge 留空，_build_elif_region 的链式兜底会把该三元区域的两臂块认作
        elif body / final_else（order_api future_order、option_order 偏移 130 的
        `if order_ is None: return None` + `if not is_trade(): strategy_log.info(
        ...format(side=... if ... else ..., ...))`，链取 merge=350 把整条语句切碎，
        strict seq_len 101→93、83→74），而把 merge 绑到 else_succ 后 else_blocks 为空，
        三元区域与其宿主语句保持同一归属。

        安全性：then 臂硬退出 ⇒「if c: 退出」+ 后续语句 与「if c: 退出 else: 后续语句」
        编译为逐字相同的指令序列（then 臂不需要 JUMP_FORWARD 到 merge），判据只改变区域
        归属。全部合取项均为同层结构事实：① then_succ 终结符属 return/raise 族；
        ② then_succ 无正常流后继（异常边除外）；③ else_succ 终结符属前向条件跳转/短路
        跳转族；④ else_succ 恰有两个条件后继；⑤ else_succ 的前驱非空且全为本 header
        （有外部前驱的场景由上文 _else_has_external_pred 分支负责，两条路径互斥）；
        ⑥ else_succ 的某后继是已识别三元区域的入口块。
        """
        _r50e_then_last = then_succ.get_last_instruction()
        if (_r50e_then_last is None
                or _r50e_then_last.opname not in ('RETURN_VALUE', 'RETURN_CONST',
                                                  'RAISE_VARARGS', 'RERAISE')):
            return False
        _r50e_exc = getattr(then_succ, 'exception_successors', set()) or set()
        if [s for s in (then_succ.successors or []) if s not in _r50e_exc]:
            return False
        _r50e_else_last = else_succ.get_last_instruction()
        if (_r50e_else_last is None
                or _r50e_else_last.opname not in
                (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)):
            return False
        if len(else_succ.conditional_successors or []) != 2:
            return False
        _r50e_preds = list(else_succ.predecessors or [])
        if not _r50e_preds or any(p is not header for p in _r50e_preds):
            return False
        for _r50e_s in (else_succ.successors or []):
            for _r50e_tr in self._filter_regions(ternary_regions or [], TernaryRegion):
                if _r50e_tr.entry is _r50e_s:
                    return True
        return False

'''
E_ANCHOR_A = '    def _compute_merge_from_jump_targets(self, header: BasicBlock,'
E_ANCHOR_B = ('                if merge is None:\n'
              '                    _then_br_role = self.get_block_role(then_succ)\n')
E_CALL = ('                # 区域归约算法原则 2（每块唯一归属）·R50-E：then 臂硬退出 +\n'
          '                # else_succ 是仅由本 header 进入、其后继含三元区域入口的条件头。\n'
          '                if merge is None and self._r50e_exit_then_head_into_ternary(\n'
          '                        block, then_succ, else_succ, ternary_regions):\n'
          '                    merge = else_succ\n')
spec_e = {'file': 'core/cfg/region_analyzer.py',
          'edits': [{'anchor': E_ANCHOR_A, 'repl': E_HELPER + E_ANCHOR_A},
                    {'anchor': E_ANCHOR_B, 'repl': E_CALL + E_ANCHOR_B}]}

for nm, sp in (('r50b', spec_b), ('r50e', spec_e)):
    out = r'D:\Temp\r50mine\spec_%s.json' % nm
    io.open(out, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(sp, ensure_ascii=False, indent=1))
    print('wrote', out)
