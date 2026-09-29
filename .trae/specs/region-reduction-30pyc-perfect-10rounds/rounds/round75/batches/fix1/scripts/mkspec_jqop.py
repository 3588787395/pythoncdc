# -*- coding: utf-8 -*-
"""fix1 jq: emit specs/jqop1.json (3 edits in core/cfg/region_ast_generator.py).

靶：jq_trans_module 两个 replace_args 单元 mandated 63/65 -> 65/65
根因：_cjb_skip_inline_if 分支丢弃块尾条件操作数（只发射前导语句就 return）。
判据：同层身份（记录挂在 fall-through 入口块，消费按 region.entry 取同一对象），
      嫁接去向由 op_chain 链内位置判定；无自增 self 状态、无跨层、无偏移阈值。
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
CORE = REPO + r'\core\cfg\region_ast_generator.py'
OUT = r'D:/Temp/opencode/r75gate/fix1/specs/jqop1.json'

raw = io.open(CORE, 'rb').read()
src = raw.decode('utf-8-sig').replace('\r\n', '\n')
lines = src.split('\n')


def block(a, b):
    return '\n'.join(lines[a - 1:b])


a1 = block(47629, 47633)
a2 = block(47639, 47643)
a3 = block(32662, 32662)

r1 = """                _cjb_skip_inline_if = False
                _cjb_pend_key = None
                if _cjb_then_entry and _cjb_then_entry not in self.generated_blocks:
                    _er = self.region_analyzer.get_entry_region_for_block(_cjb_then_entry)
                    if _er and _er.entry == _cjb_then_entry and isinstance(_er, RegionASTGenerator._ALL_REGION_TYPES):
                        _cjb_skip_inline_if = True
                        _cjb_pend_key = _cjb_then_entry"""

r2 = """                if _cjb_skip_inline_if:
                    if _cjb_pre_stmts:
                        stmts.extend(_cjb_pre_stmts)
                    if _cjb_pend_key is not None and _cjb_pure_cond:
                        _pend_expr = _cjb_cond_expr
                        if (isinstance(_pend_expr, dict)
                                and not (_pend_expr.get('type') == 'Constant'
                                         and _pend_expr.get('value') is True)):
                            _pend_op = ('and' if ('FALSE' in _cond_jump_bs.opname)
                                        != bool(_cjb_negate) else 'or')
                            setattr(_cjb_pend_key, '_leading_operand',
                                    (_pend_expr, _pend_op, _cjb_jump_target))
                    self.generated_blocks.add(block)
                    return stmts"""

r3_body = '''    def _graft_pending_operand(self, region, expr):
        """[R75 fix1] 把 _cjb_skip_inline_if 丢掉的前置条件操作数接回后继区域的条件。

        ① 根因（丢弃点）：_generate_block_statements_body 在「块尾条件跳转的
           fall-through 恰是某区域 entry」时只发射前导语句就 return，该块重建成的
           纯条件操作数（_cjb_cond_expr）没有进入后继区域的操作数链，于是
           `'(' in s and ')' not in s or '[' in s and ']' not in s` 退化成
           `')' not in s or '[' in s and ']' not in s`（jq_trans_module 的两个
           replace_args 单元被判 Different control flow，63/65）。
        ② 同层身份判据：记录挂在 fall-through 入口块上（_leading_operand），消费端
           按 region.entry 取同一个块对象配对；不跨层（不用 region.entry in r.blocks），
           不用函数名/文件名/偏移阈值/名字白名单，也不新增 self 状态。
        ③ 去向与守卫：由 op_chain 的链内位置决定——跳转目标是链出口或 merge_block
           时整体相接，是链首后续成员（ck==1 且链首自成一组）时接进首组，其余原样
           返回；_contains_identity 保证同一表达式被多条路径消费时只嫁接一次。
        """
        rec = getattr(getattr(region, 'entry', None), '_leading_operand', None)
        if not rec or not isinstance(expr, dict):
            return expr
        operand, link_op, jump_target = rec
        if jump_target is None or self._contains_identity(expr, operand):
            return expr
        _merge = getattr(region, 'merge_block', None)
        _merge_off = getattr(_merge, 'start_offset', None)
        _chain = list(getattr(region, 'op_chain', None) or ())
        _starts = set()
        _exits = set()
        for _cb, _co in _chain:
            _starts.add(getattr(_cb, 'start_offset', None))
            _li = _cb.get_last_instruction()
            if _li is not None and getattr(_li, 'argval', None) is not None:
                if _li.argval not in _starts:
                    _exits.add(_li.argval)
        if _merge_off is not None:
            _exits.add(_merge_off)
        ck = None
        for _i, (_cb, _co) in enumerate(_chain):
            if getattr(_cb, 'start_offset', None) == jump_target:
                ck = _i
                break
        if ck is None:
            if jump_target in _exits:
                return {'type': 'BoolOp', 'op': link_op, 'values': [operand, expr]}
            return expr
        if ck == 1 and len(_chain) >= 2 and _chain[0][1] != _chain[1][1]:
            if expr.get('type') != 'BoolOp' or expr.get('op') != _chain[0][1]:
                return expr
            values = list(expr.get('values') or [])
            if not values or link_op == expr.get('op'):
                return expr
            return dict(expr, values=[{'type': 'BoolOp', 'op': link_op,
                                       'values': [operand, values[0]]}] + values[1:])
        return expr
'''

r3 = '''    def _contains_identity(self, node, target):
        """[R75 fix1] AST 子树里是否已含 target 节点（按对象身份判定）——
        同一条件表达式可能被多条路径消费，用身份判定保证嫁接幂等。"""
        if node is target:
            return True
        if isinstance(node, dict):
            return any(self._contains_identity(v, target) for v in node.values())
        if isinstance(node, list):
            return any(self._contains_identity(v, target) for v in node)
        return False

''' + r3_body + '''
    def _build_boolop_expression(self, region: 'BoolOpRegion', skip_elif_blocks: bool = True) -> Optional[Dict[str, Any]]:
        """[R75 fix1] 对外入口：先按原算法重建布尔表达式，再嫁接被丢掉的前置操作数。"""
        return self._graft_pending_operand(
            region, self._build_boolop_expression_inner(region, skip_elif_blocks))

    def _build_boolop_expression_inner(self, region: 'BoolOpRegion', skip_elif_blocks: bool = True) -> Optional[Dict[str, Any]]:'''

edits = [{'anchor': a1, 'repl': r1},
         {'anchor': a2, 'repl': r2},
         {'anchor': a3, 'repl': r3}]

patched = src
for i, e in enumerate(edits):
    n = patched.count(e['anchor'])
    assert n == 1, 'edit %d anchor count=%d' % (i, n)
    patched = patched.replace(e['anchor'], e['repl'])
assert patched != src
os.makedirs(os.path.dirname(OUT), exist_ok=True)
spec = {'file': 'core/cfg/region_ast_generator.py', 'edits': edits}
io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('wrote %s  edits=%d lines %d -> %d' % (OUT, len(edits),
                                             src.count('\n'), patched.count('\n')))
compile(patched, CORE, 'exec')
print('compile OK')
