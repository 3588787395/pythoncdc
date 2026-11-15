# -*- coding: utf-8 -*-
"""rr-v5r173 patch — cookiejar CJ2 CHAINASSIGN (`self._policy._now = self._now = v`).

Applies the r173 edit with count==1 anchors, utf-8-sig (BOM aware) + newline
preserving (LF-space edit, CRLF restore), py_compile validation and full
idempotency.

usage:  D:/Python/python.exe -I -X utf8 fix173.py [--root <repo-root>] [--check]
"""
import argparse
import hashlib
import os
import py_compile
import sys

REPO = 'F:/Downloads/pythoncdc-main'

_OLD = '''                pre_instrs.append(instr)
                # [v99-CHAINALIAS] 与上方 STORE_SUBSCR 分支同一前瞻归约
                # （复杂属性目标链 `o.a = alias = v`，同一字节码事实同语义，
                # C2）；pre_unpack_info 形态已在上方整条消费不受影响。
                _v99_nxt = None
                _v99_ni = _instr_idx + 1
                while _v99_ni < len(_iter_instrs):
                    _v99_n = _iter_instrs[_v99_ni]
                    if _v99_n.opname in ('RESUME', 'NOP', 'CACHE'):
                        _v99_ni += 1
                        continue
                    _v99_nxt = _v99_n
                    break
                if (_v99_nxt is not None
                        and _v99_nxt.opname in ('STORE_FAST', 'STORE_NAME',
                                                'STORE_GLOBAL', 'STORE_DEREF')):
                    _v99_chain = self._build_complex_name_chain_assign(
                        pre_instrs + [_v99_nxt])
                    if _v99_chain is not None:
                        pre_stmts.append(_v99_chain)
                        pre_seen_store = True
                        pre_instrs = []
                        _c2_skip_until = _v99_ni + 1
                        continue
                stmt = self._build_attr_assign(pre_instrs)
'''

_NEW = '''                pre_instrs.append(instr)
                # [CJ2-r173] 链式属性目标值链保持（判据与
                # _generate_block_statements_body 的 STORE_ATTR 分支同源）：
                # pre_instrs 含本 STORE（其自身 -2 已计入），弹后净栈深仍 > 0
                # ⇒ 值是 COPY 复制出来的链式份额，后续目标段仍待消费
                # （``o.a = o.b = x`` 的协议：值; COPY 1; [对象; STORE_ATTR]×N，
                # 每段净 -1）——不在此切分语句，否则尾目标会被
                # _build_attr_assign 静默丢成单目标赋值（cookiejar
                # ``self._policy._now = self._now = int(time.time())`` 族）。
                # 判据只读块内 opcode 序 + CPython 值栈净效应；单目标赋值弹后
                # 恒为 0，不命中（行为逐位不变）。
                _b107_d = 0
                _b107_dok = True
                for _b107_di in pre_instrs:
                    _b107_eff = self._instruction_stack_effect(_b107_di)
                    if _b107_eff is None:
                        _b107_dok = False
                        break
                    _b107_d += _b107_eff
                if _b107_dok and _b107_d > 0:
                    # 仅当链的下一目标仍是复杂目标（STORE_ATTR/STORE_SUBSCR）
                    # 时保持累积；`o.a = x = v` 的尾目标是简单名，须让下方
                    # v99-CHAINALIAS 前瞻按复杂目标 + 尾随名整链归约（否则
                    # 首复杂目标被 B107 前缀吞并、尾名单独成句，difflib
                    # SequenceMatcher.__chain_b 的 `self.bjunk = junk = set()`
                    # 实测丢属性目标）。
                    _b107_nxt = None
                    _b107_ni = _instr_idx + 1
                    while _b107_ni < len(_iter_instrs):
                        _b107_n = _iter_instrs[_b107_ni]
                        if _b107_n.opname in ('RESUME', 'NOP', 'CACHE'):
                            _b107_ni += 1
                            continue
                        if _b107_n.opname in ('STORE_ATTR', 'STORE_SUBSCR',
                                              'STORE_FAST', 'STORE_NAME',
                                              'STORE_GLOBAL', 'STORE_DEREF'):
                            _b107_nxt = _b107_n
                            break
                        if _b107_n.opname in ('POP_TOP', 'RETURN_VALUE',
                                              'RETURN_CONST', 'RAISE_VARARGS'):
                            break
                        _b107_ni += 1
                    if (_b107_nxt is not None
                            and _b107_nxt.opname in ('STORE_ATTR', 'STORE_SUBSCR')):
                        continue
                # [v99-CHAINALIAS] 与上方 STORE_SUBSCR 分支同一前瞻归约
                # （复杂属性目标链 `o.a = alias = v`，同一字节码事实同语义，
                # C2）；pre_unpack_info 形态已在上方整条消费不受影响。
                _v99_nxt = None
                _v99_ni = _instr_idx + 1
                while _v99_ni < len(_iter_instrs):
                    _v99_n = _iter_instrs[_v99_ni]
                    if _v99_n.opname in ('RESUME', 'NOP', 'CACHE'):
                        _v99_ni += 1
                        continue
                    _v99_nxt = _v99_n
                    break
                if (_v99_nxt is not None
                        and _v99_nxt.opname in ('STORE_FAST', 'STORE_NAME',
                                                'STORE_GLOBAL', 'STORE_DEREF')):
                    _v99_chain = self._build_complex_name_chain_assign(
                        pre_instrs + [_v99_nxt])
                    if _v99_chain is not None:
                        pre_stmts.append(_v99_chain)
                        pre_seen_store = True
                        pre_instrs = []
                        _c2_skip_until = _v99_ni + 1
                        continue
                # [B107] 链式属性目标整链归约（复杂 STORE 数 >= 2；首段已在
                # 上方按净栈深保持累积，末段弹后归零即整链归约为单一 Assign）。
                _b107_chain = self._build_chained_complex_target_assign(pre_instrs)
                if _b107_chain is not None:
                    pre_stmts.append(_b107_chain)
                    pre_seen_store = True
                    pre_instrs = []
                    continue
                stmt = self._build_attr_assign(pre_instrs)
'''

_ANCHOR = """        self._generating_regions.discard(region_id)
        self._generated_regions.add(region_id)
        if_result = result
        if pre_stmts:
            if_result = pre_stmts + [if_result]
"""

_GUARD = """        self._generating_regions.discard(region_id)
        self._generated_regions.add(region_id)
        # [CJ2-r173b] 共同早退守卫链整链归约：`if c1: if c2: ... <body>` 各层
        # 假边同落一个终结 merge（如 `return []`）时，区域归约把续体当 then 臂、
        # 把共同假臂留给父序列在 body 之后发射，产物成为
        # `if c1 and c2: <body>` + 末尾 `if not cN: return []`——守卫被挪到
        # body 之后（cookiejar make_cookies 的
        # `if ((not A and not B) or (not B and not C) or ...): return []` 实测）。
        # 判据（本区域自身块结构 + 已重建 AST 形状，无名字/常量/偏移阈值）：
        # ① 非循环上下文且本 if 无 orelse；② merge_block 存在、终结于
        # RETURN_*/RAISE_VARARGS、不在 then_blocks 且 then 各块后继不含 merge
        # （then 不可达 merge ⇒ merge 只服务假边）；③ 测试为 BoolOp('and')
        # 且合取支 >= 2；④ body 末条是「not(BoolOp) -> 终结臂」的取反守卫，
        # body 其余部分以同形正极性 BoolOp('or') 守卫开头（可多层）；⑤ 不存在
        # 同 merge 的更外层 IfRegion（内层由本最外层一并归约，避免内层先被
        # 改写成 not 形后外层折叠出错误极性）。
        # 归约：`If(not(c1 and ... and cN), merge 臂, None)` + 续体语句；
        # 重编译时 CPython 对 not(and(or...)) 的 De Morgan 展开逐字节再生
        # 原始「或链 + 单 return 块」布局（`if not ((A or B) and ...): return []`
        # 与源码 DNF 的 co_code 实测逐条相同）。
        # C3：任一判据不满足时 result 原样保留，其余区域行为逐位不变。
        _v173_rewrite = None
        if (self._current_loop is None
                and getattr(region, 'entry', None) is not None
                and isinstance(result, dict) and result.get('type') == 'If'
                and not result.get('orelse')
                and isinstance(result.get('test'), dict)
                and result['test'].get('type') == 'BoolOp'
                and result['test'].get('op') == 'and'
                and len(result['test'].get('values') or []) >= 2
                and isinstance(result.get('body'), list)
                and len(result.get('body')) >= 2
                and getattr(region, 'merge_block', None) is not None):
            _v173_mb = region.merge_block
            _v173_mb_last = _v173_mb.get_last_instruction()
            _v173_then = list(getattr(region, 'then_blocks', None) or [])
            if (_v173_mb not in _v173_then
                    and _v173_mb_last is not None
                    and _v173_mb_last.opname in ('RETURN_VALUE', 'RETURN_CONST',
                                                 'RAISE_VARARGS')):
                _v173_outermost = not any(
                    _v173_r is not region and isinstance(_v173_r, IfRegion)
                    and getattr(_v173_r, 'merge_block', None) is _v173_mb
                    and getattr(_v173_r, 'entry', None) is not None
                    and _v173_r.entry.start_offset < region.entry.start_offset
                    for _v173_r in self.region_analyzer.regions)
                if _v173_outermost:
                    _v173_body = list(result['body'])
                    _v173_guard = _v173_body[-1]
                    if (isinstance(_v173_guard, dict)
                            and _v173_guard.get('type') == 'If'
                            and not _v173_guard.get('orelse')
                            and isinstance(_v173_guard.get('test'), dict)
                            and _v173_guard['test'].get('type') == 'UnaryOp'
                            and _v173_guard['test'].get('op') == 'not'
                            and isinstance(_v173_guard['test'].get('operand'), dict)
                            and _v173_guard['test']['operand'].get('type') == 'BoolOp'
                            and _v173_guard.get('body')):
                        _v173_conds = list(result['test'].get('values') or [])
                        _v173_conds.append(_v173_guard['test']['operand'])
                        _v173_rest = _v173_body[:-1]
                        _v173_depth = 0
                        while (len(_v173_rest) == 1 and _v173_depth < 16
                               and isinstance(_v173_rest[0], dict)
                               and _v173_rest[0].get('type') == 'If'
                               and not _v173_rest[0].get('orelse')
                               and isinstance(_v173_rest[0].get('test'), dict)
                               and _v173_rest[0]['test'].get('type') == 'BoolOp'
                               and _v173_rest[0]['test'].get('op') == 'or'):
                            _v173_depth += 1
                            _v173_conds.insert(-1, _v173_rest[0]['test'])
                            _v173_rest = list(_v173_rest[0].get('body') or [])
                        if (_v173_rest
                                and all(isinstance(_v173_c, dict)
                                        for _v173_c in _v173_conds)):
                            _v173_rewrite = [
                                {'type': 'If',
                                 'test': _negate_expr({'type': 'BoolOp', 'op': 'and',
                                                       'values': _v173_conds}),
                                 'body': list(_v173_guard.get('body') or []),
                                 'orelse': None}] + _v173_rest
        if _v173_rewrite is not None:
            result = _v173_rewrite
        # 记录本区域产出的顶层 If 节点（供上层 merge 提升判据按「每块唯一
        # 归属」精确匹配：只有 merge_block 自己产出的 If 才可提升）。
        if getattr(region, 'entry', None) is not None:
            for _v173_node in (result if isinstance(result, list) else [result]):
                if (isinstance(_v173_node, dict)
                        and _v173_node.get('type') == 'If'):
                    _v173_node['_v173_entry'] = region.entry.start_offset
        # [CJ2-r173c] merge 块是下一兄弟 IfRegion 入口时的语句提升：顺序
        # `if X: <body>` / `if Y:` 的 merge 块恰为后一个 if 的 entry，但生成
        # 层把该 If 追加到了前一个 if 的 then 体末尾，产物把它缩进进 then 体内
        # （cookiejar make_cookies `if rfc2965: …` 之后的 `if ns_cookies:` 实测）。
        # 判据（块结构 + 已重建 AST 形状）：① merge_block 存在且不在
        # then_blocks；② merge_block 的入口区域是 IfRegion（按「每块唯一
        # 归属」该块语句由该 IfRegion 认领）；③ 当前结果末条是无 orelse 的
        # If，且其 body 末条是 If（即被错误嵌套的 merge 块语句）。
        # 归约：把该 If 提升为外层语句的兄弟，外层 If 保持原块归属；不新增/
        # 不删除任何块，不改变 region 的 then/else/merge 登记。
        # C3：任一判据不满足时 result 原样保留。
        _v173_mb_region = None
        if (self._current_loop is None
                and getattr(region, 'merge_block', None) is not None
                and region.merge_block not in (getattr(region, 'then_blocks', None) or [])):
            _v173_mbr = self.region_analyzer.get_entry_region_for_block(region.merge_block)
            _v173_cb = getattr(region, 'condition_block', None) or region.entry
            _v173_cb_last = (_v173_cb.get_last_instruction()
                             if _v173_cb is not None else None)
            if (isinstance(_v173_mbr, IfRegion)
                    and getattr(_v173_mbr, 'entry', None) is region.merge_block
                    and _v173_cb_last is not None
                    and 'JUMP' in _v173_cb_last.opname
                    and _v173_cb_last.argval == region.merge_block.start_offset):
                _v173_mb_region = _v173_mbr
        if _v173_mb_region is not None:
            _v173_seq = result if isinstance(result, list) else [result]
            if (_v173_seq and isinstance(_v173_seq[-1], dict)
                    and _v173_seq[-1].get('type') == 'If'
                    and not _v173_seq[-1].get('orelse')
                    and isinstance(_v173_seq[-1].get('body'), list)
                    and len(_v173_seq[-1]['body']) >= 1
                    and isinstance(_v173_seq[-1]['body'][-1], dict)
                    and _v173_seq[-1]['body'][-1].get('type') == 'If'
                    and _v173_seq[-1]['body'][-1].get('_v173_entry')
                    == region.merge_block.start_offset):
                _v173_outer = dict(_v173_seq[-1])
                _v173_moved = _v173_outer['body'][-1]
                _v173_outer['body'] = list(_v173_outer['body'][:-1])
                result = list(_v173_seq[:-1]) + [_v173_outer, _v173_moved]
        if_result = result
        if pre_stmts:
            if_result = pre_stmts + ([if_result] if isinstance(if_result, dict)
                                     else list(if_result))
"""

EDITS = [
    ('core/cfg/region_ast_generator.py', _OLD, _NEW, 'CJ2-CHAINASSIGN'),
    ('core/cfg/region_ast_generator.py', _ANCHOR, _GUARD, 'CJ2-GUARDCHAIN'),
]


def read_bom_aware(path):
    """Return (text in LF space, has_bom, is_crlf) without touching the file."""
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    crlf = raw.count(b'\r\n') > 0 and raw.count(b'\r\n') == raw.count(b'\n')
    return raw.decode('utf-8-sig').replace('\r\n', '\n'), bom, crlf


def write_bom_aware(path, text, bom, crlf):
    data = (text.replace('\n', '\r\n') if crlf else text).encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    with open(path, 'wb') as f:
        f.write(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=REPO)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    root = args.root

    texts = {}
    boms = {}
    crlfs = {}
    for rel, old, new, tag in EDITS:
        p = os.path.join(root, rel)
        if rel not in texts:
            texts[rel], boms[rel], crlfs[rel] = read_bom_aware(p)
        cur = texts[rel]
        if new in cur:
            print('  [skip] %-32s already applied (%s)' % (tag, rel))
            continue
        n = cur.count(old)
        if n != 1:
            print('  [FAIL] %-32s anchor count=%d (expected 1) in %s'
                  % (tag, n, rel))
            return 2
        texts[rel] = cur.replace(old, new, 1)
        print('  [apply] %-31s %s' % (tag, rel))

    for rel, text in texts.items():
        p = os.path.join(root, rel)
        if args.check:
            print('  [check] %s would be %d bytes'
                  % (rel, len(text.encode('utf-8'))))
            continue
        write_bom_aware(p, text, boms[rel], crlfs[rel])
        py_compile.compile(p, doraise=True)
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
        print('  [wrote] %-28s %d bytes sha16=%s'
              % (rel, os.path.getsize(p), h))
    return 0


if __name__ == '__main__':
    sys.exit(main())
