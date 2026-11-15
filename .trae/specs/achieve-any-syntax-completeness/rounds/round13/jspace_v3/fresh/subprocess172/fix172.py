# -*- coding: utf-8 -*-
"""rr-v5r172 patch — subprocess SP2 RAISE-EXPR + SP8 IFMERGE.

Applies the r172 edits to the pristine tree (HEAD) with count==1 anchors,
utf-8-sig (BOM aware) + newline preserving (LF-space edit, CRLF restore),
py_compile validation and full idempotency.

usage:  D:/Python/python.exe -I -X utf8 fix172.py [--root <repo-root>] [--check]
"""
import argparse
import hashlib
import io
import os
import py_compile
import sys

REPO = 'F:/Downloads/pythoncdc-main'

# (relative path, old, new, tag)
EDITS = [
    ('core/cfg/region_analyzer.py',
     '            existing_entry_regions = [r for r in self.regions if type(r) is TryExceptRegion and r.entry == entry_block]\n            if existing_entry_regions:\n                for existing in existing_entry_regions:\n                    if (existing.try_offset_start >= try_start and\n                            existing.try_offset_end <= try_end and\n                            existing.try_offset_end < try_end):\n',
     "            existing_entry_regions = [r for r in self.regions if type(r) is TryExceptRegion and r.entry == entry_block]\n            if existing_entry_regions:\n                for existing in existing_entry_regions:\n                    # [v172-TRYNEST] 嵌套 try（内外层共享入口块）不拆入口：\n                    # existing 的 try 体块集是本 region try_blocks 的真子集时，\n                    # 它是本 region 保护跨度内部的内层 try（try-in-try），两者\n                    # 入口必须保持共享，由生成层 nested_try_regions 预循环把内层\n                    # 作为抽象节点整树嵌套进外层 Try.body（入口引用也由\n                    # get_entry_region_for_block 的同入口嵌套裁决交还外层）。\n                    # 若按「同入口兄弟 region」把外层入口下移到\n                    # existing.try_offset_end，内层 try 会被父级块走查提前发射成\n                    # 兄弟语句：外层 try 体被切成「内层 try 之后」的续体，异常表\n                    # 少掉覆盖内层 finally 正常副本的那一条区间\n                    # （subprocess._execute_child 逐字复现）。同入口、非嵌套的\n                    # 双 region 形态（try/except 与 try/finally 覆盖同一 try 体）\n                    # 两侧 try 体块集相等，不命中本守卫，入口调整行为逐位不变（C3）。\n                    if (getattr(existing, 'try_blocks', None) and try_blocks\n                            and set(existing.try_blocks) < set(try_blocks)):\n                        continue\n                    if (existing.try_offset_start >= try_start and\n                            existing.try_offset_end <= try_end and\n                            existing.try_offset_end < try_end):\n",
     'insert'),
    ('core/cfg/region_analyzer.py',
     "                        # (missing .error), causing _generate_ternary to generate\n                        # `app_log(ternary)` instead of `app_log.error(format(ternary))`.\n                        _func_expr = {'type': 'Name', 'id': func_i.argval, 'ctx': 'Load'}\n                        _obj_chain_idx = push_null_idx + 2\n                        while _obj_chain_idx < len(instrs):\n                            _chain_i = instrs[_obj_chain_idx]\n                            # LOAD_ATTR after the base object extends the method chain\n",
     "                        # (missing .error), causing _generate_ternary to generate\n                        # `app_log(ternary)` instead of `app_log.error(format(ternary))`.\n                        _func_expr = {'type': 'Name', 'id': func_i.argval, 'ctx': 'Load'}\n                        # [v172-FUNCCHAIN] 属性链起点按 NULL 的落位区分：\n                        # 显式 PUSH_NULL 形态为 [PUSH_NULL, LOAD_*, LOAD_ATTR…]，\n                        # 链从 push_null_idx+2 起；implicit-NULL 形态\n                        # （LOAD_GLOBAL arg&1，NULL 与可调用对象同占一条指令）\n                        # 为 [LOAD_*, LOAD_ATTR…]，链从 push_null_idx+1 起。\n                        # 旧式恒取 +2 会跳过 implicit-NULL 形态紧跟的首个实参\n                        # 装载指令，把下一条 LOAD_ATTR 误接到可调用对象上：\n                        # `TimeoutExpired(self.args, …)` 被重建成\n                        # `TimeoutExpired.args(…)`——LOAD_METHOD 形态，co_code\n                        # 与 orig 不一致且首实参被偷（Popen._check_timeout 实测）。\n                        # 判据 = 同块指令族（PUSH_NULL 是否存在），无名字/偏移白名单。\n                        _obj_chain_idx = push_null_idx + (\n                            2 if instrs[push_null_idx].opname == 'PUSH_NULL' else 1)\n                        while _obj_chain_idx < len(instrs):\n                            _chain_i = instrs[_obj_chain_idx]\n                            # LOAD_ATTR after the base object extends the method chain\n",
     'replace'),
    ('core/cfg/region_analyzer.py',
     '            fixed_chain.append((block, op_type))\n        return fixed_chain\n\n    def _boolop_chain_exits_are_distinct_sinks(self, chain: List[Tuple[BasicBlock, str]]) -> bool:\n        """[R4-B116 sinkexit] 短路链出口是否为「≥2 个互不相同的终结隐式 return None 块」。\n\n',
     '            fixed_chain.append((block, op_type))\n        return fixed_chain\n\n    def _v172_negated_and_operand_op_types(self, chain: List[Tuple[BasicBlock, str]]) -> List[Tuple[BasicBlock, str]]:\n        """负极性 and 操作数（`not X`）的链内 op 归正。\n\n        [v172-NEGAND] ①算法依据：CPython 3.11 在条件语境把 `not X` 编译成\n        「X 为真 ⇒ 整链失败」的跳转，故 `A and not B` 与 `A and (B or C)` 的\n        成员块末指令族相同（TRUE 极性条件跳转），区别只在跳转目标的角色：\n        - `not B` 的 TRUE 目标 = 本 and 链的失败出口（末成员 FALSE 跳转目标，\n          即 merge/else）；\n        - 嵌套 or 组首位成员的 TRUE 目标 = 组内真出口 T ≠ merge（组末成员\n          以 FALSE 极性落到 merge）。\n        逐指令 `\'and\' if FALSE else \'or\'` 分类把 ① 错标 \'or\'，随后 or 分组建\n        设器把该成员与后继成员并成 `(X or Y ...)`——极性反转（`not close_fds`\n        变 `close_fds`）且比较运算被编译器二次取反（Popen._execute_child 的\n        posix_spawn 复合条件实测：3 个 TRUE 极性成员错标 \'or\'，产品\n        `(close_fds or pass_fds or cwd is None)` / `(start_new_session or\n        process_group == -1)`）。\n\n        ②归约顺序：紧随 `_normalize_none_check_op_types`，在 or 分组/发射之前\n        把标签归正为 \'and\'；操作数极性由构建层按跳转方向（TRUE 极性 ⇒ 隐式\n        `not`）逐项还原，与 W14-A「混合极性链由构建层 implicit-not 还原」同\n        口径（真值表与 co_code 均还原）。\n\n        ③唯一归属/判据（全部同层块结构事实）：链内同时存在 \'and\' 与 \'or\'\n        标签；末成员标签为 \'and\' 且末指令是失败极性跳转（opname 含 \'FALSE\'，\n        即 and 链的短路出口）⇒ exit_off = 其跳转目标；末尾成员 fall-through\n        后继 ≠ exit（排除 `if A and (B or C): pass` 这类 body 与 exit 重合的\n        歧义形态，该形态下 TRUE 目标与 exit 同块，不可判别极性）。\n\n        ④嵌套处理：只改标签，不认领块、不建区域、不动异常表/循环表。\n\n        ⑤入口引用语义：返回同长度链（成员与顺序逐位不变），仅 op 字段可能\n        由 \'or\' 改 \'and\'。\n\n        ⑥反编译流程：_create_boolop_region_from_chain（BoolOpRegion 唯一创建\n        点）入口归一化 → op_chain → _build_boolop_expression* / or 分组发射。\n\n        C 条款：[C1] 只读链成员末指令 opname/argval 与后继集合；[C2] 判据只\n        命中「TRUE 极性且目标 = and 链出口」的成员，其余逐位保持（无 \'or\'\n        成员命中时原链原样返回）；[C3] 不命中即返回原对象，无语义/发射差。\n        """\n        if not chain or len(chain) < 2:\n            return chain\n        ops = {op for _, op in chain}\n        if \'and\' not in ops or \'or\' not in ops:\n            return chain\n        last_block, last_op = chain[-1]\n        if last_op != \'and\':\n            return chain\n        last_i = last_block.get_last_instruction()\n        if last_i is None or getattr(last_i, \'argval\', None) is None:\n            return chain\n        if \'FALSE\' not in last_i.opname:\n            return chain\n        exit_off = last_i.argval\n        then_body = None\n        for _s in last_block.conditional_successors:\n            if _s.start_offset != exit_off:\n                then_body = _s\n                break\n        if then_body is None or then_body.start_offset == exit_off:\n            return chain\n        fixed = []\n        changed = False\n        for block, op in chain:\n            if op == \'or\':\n                _li = block.get_last_instruction()\n                if (_li is not None and \'TRUE\' in _li.opname\n                        and getattr(_li, \'argval\', None) == exit_off):\n                    op = \'and\'\n                    changed = True\n            fixed.append((block, op))\n        return fixed if changed else chain\n\n    def _boolop_chain_exits_are_distinct_sinks(self, chain: List[Tuple[BasicBlock, str]]) -> bool:\n        """[R4-B116 sinkexit] 短路链出口是否为「≥2 个互不相同的终结隐式 return None 块」。\n\n',
     'insert'),
    ('core/cfg/region_analyzer.py',
     '        的全部调用点均经此），拒绝即整条链不产区域，不存在旁路创建。\n        """\n        chain = self._normalize_none_check_op_types(chain)\n        # [R14b·W14-D 门控细化] 属性链回溯放行（首成员尾部为\n        # LOAD_ATTR/LOAD_METHOD 的真值测试）时，若首块前置语句的存储目标被\n        # 后续链成员的操作数读取（如 exc_from_type = getattr(...);\n',
     '        的全部调用点均经此），拒绝即整条链不产区域，不存在旁路创建。\n        """\n        chain = self._normalize_none_check_op_types(chain)\n        chain = self._v172_negated_and_operand_op_types(chain)\n        # [R14b·W14-D 门控细化] 属性链回溯放行（首成员尾部为\n        # LOAD_ATTR/LOAD_METHOD 的真值测试）时，若首块前置语句的存储目标被\n        # 后续链成员的操作数读取（如 exc_from_type = getattr(...);\n',
     'insert'),
    ('core/cfg/region_analyzer.py',
     "            return None\n        if len(_matching) == 1:\n            return _matching[0]\n        _type_priority = {\n            'WithRegion': 6, 'TryExceptRegion': 5, 'MatchRegion': 4,\n            'BoolOpRegion': 3, 'TernaryRegion': 3, 'IfRegion': 2, 'LoopRegion': 0\n",
     "            return None\n        if len(_matching) == 1:\n            return _matching[0]\n        # [v172-NESTED-TRY] 同入口嵌套 try：两个 TryExceptRegion 以同一块为入口\n        # 且保护跨度互相包含（内层跨度 ⊂ 外层跨度）时，入口引用语义归外层\n        # （原则 3 嵌套即抽象节点 + 原则 4 父引用子入口）——外层 Try.body 的\n        # nested_try_regions 预循环会把内层整树嵌套发射。若这里返回内层，父级\n        # 块走查会先发射内层 try，外层 try 体被切成「内层之后」的续体：异常表\n        # 少掉覆盖内层 finally 正常副本的那条区间、外层保护起点右移\n        # （subprocess._execute_child 实测）。判据 = 同入口 + 保护跨度包含关系\n        # （区域成员事实），无偏移/名字白名单。\n        _nr_try_matches = [r for r in _matching if isinstance(r, TryExceptRegion)]\n        if len(_nr_try_matches) > 1:\n            for _nr_cand in _nr_try_matches:\n                _nr_cs = getattr(_nr_cand, 'try_offset_start', None)\n                _nr_ce = getattr(_nr_cand, 'try_offset_end', None)\n                if _nr_cs is None or _nr_ce is None:\n                    continue\n                for _nr_other in _nr_try_matches:\n                    if _nr_other is _nr_cand:\n                        continue\n                    _nr_os = getattr(_nr_other, 'try_offset_start', None)\n                    _nr_oe = getattr(_nr_other, 'try_offset_end', None)\n                    if _nr_os is None or _nr_oe is None:\n                        continue\n                    if (_nr_cs <= _nr_os and _nr_oe <= _nr_ce\n                            and (_nr_cs, _nr_ce) != (_nr_os, _nr_oe)):\n                        return _nr_cand\n        _type_priority = {\n            'WithRegion': 6, 'TryExceptRegion': 5, 'MatchRegion': 4,\n            'BoolOpRegion': 3, 'TernaryRegion': 3, 'IfRegion': 2, 'LoopRegion': 0\n",
     'insert'),
    ('core/cfg/region_ast_generator.py',
     '                              or handler_in_range or _is_span_contained)\n                             and not _is_in_if_branch\n                             and not _is_inside_intermediate_loop)\n                if is_nested and (r.parent is None or r.parent is region):\n                    nested_is_smaller = r.try_offset_end - r.try_offset_start < region.try_offset_end - region.try_offset_start\n                    if nested_is_smaller or is_child_in_try:\n                        nested_try_regions.append(r)\n',
     '                              or handler_in_range or _is_span_contained)\n                             and not _is_in_if_branch\n                             and not _is_inside_intermediate_loop)\n                # [v172-NESTED-TRY] 嵌套 try 归属放宽：内层 try 的保护跨度完全\n                # 包含于外层跨度（_is_span_contained）时，内层恒为外层 try 体的\n                # 抽象节点——即使二者的 parent 都被登记成同一个祖先 IfRegion\n                # （subprocess._execute_child 的 `try: try: ... finally: ...` 实测：\n                # 内外层 parent 同为 posix_spawn IfRegion）。原 parent 等同判据在\n                # 此形态拒收，内层 try 既不嵌套也不由父级块走查发射，整段\n                # try 体语句蒸发。判据 = 保护跨度包含（区域成员事实），parent\n                # 等同判据逐位保留（C3）。\n                if is_nested and (r.parent is None or r.parent is region\n                                  or _is_span_contained):\n                    nested_is_smaller = r.try_offset_end - r.try_offset_start < region.try_offset_end - region.try_offset_start\n                    if nested_is_smaller or is_child_in_try:\n                        nested_try_regions.append(r)\n',
     'replace'),
    ('core/cfg/region_ast_generator.py',
     "            for b in tr.blocks:\n                self.generated_blocks.add(b)\n\n        return {'type': 'Expr', 'value': call_expr}\n\n\n",
     "            for b in tr.blocks:\n                self.generated_blocks.add(b)\n\n        # [v172-RAISE-EXPR] 三元作为 raise 的异常实参（最终合并块以\n        # RAISE_VARARGS 1 收尾）时，整条重建是 raise 语句而非表达式语句：\n        # 返回 Raise(call_expr)，发射层产出 `raise f(x=ternary)`。只返回 Expr\n        # 会丢 RAISE_VARARGS、尾块被补隐式 return None（co_code 少 RAISE_VARARGS\n        # 多 LOAD_CONST None + RETURN_VALUE，Popen._check_timeout 实测）。\n        # `raise E(...) from cause` 的 cause 占三元之外的栈槽，不在本路径，\n        # RAISE_VARARGS 2 逐位回落既有 Expr 行为（C3）。\n        _v172_tail_i = final_merge.get_last_instruction()\n        if (_v172_tail_i is not None\n                and _v172_tail_i.opname == 'RAISE_VARARGS'\n                and getattr(_v172_tail_i, 'arg', None) == 1):\n            return {'type': 'Raise', 'exc': call_expr, 'cause': None}\n        return {'type': 'Expr', 'value': call_expr}\n\n\n",
     'insert'),
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
