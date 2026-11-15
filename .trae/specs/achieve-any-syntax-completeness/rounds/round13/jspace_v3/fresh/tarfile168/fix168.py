#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r168 修 tarfile「族 E：`%`-format→f-string 组蒸发 + 循环尾守卫退化成裸 Expr」。

两面同轮（recon 实测只修一面 tarfile 仍 150/151）
------------------------------------------------------------
E1（组丢失）：`TarFile.list` 的
  `_safe_print(f"{t.uname or t.uid}/{t.gname or t.gid}")` 在字节码里是一条
  调用语句横跨 4 个基本块：
    @188 LOAD_GLOBAL _safe_print; t.uname; JUMP_IF_TRUE_OR_POP→@226
    @214 t.uid
    @226 FORMAT_VALUE; LOAD_CONST '/'; t.gname; JUMP_IF_TRUE_OR_POP→@256
    @244 t.gid
    @256 FORMAT_VALUE; BUILD_STRING 3; PRECALL; CALL; POP_TOP
  分析器把两条 or 链各注册成 BoolOpRegion（链 1 merge = @226 = 链 2 entry），
  两次归约各只覆盖半条语句：链 1 的 `_operand()` 丢掉 LOAD_GLOBAL 宿主、
  链 2 的 merge 块首 FORMAT_VALUE/BUILD_STRING 被后续 if 的条件提取当前导丢弃
  ⇒ 群里只剩 `tarinfo.uname or tarinfo.uid` / `tarinfo.gid` 两条裸 Expr，
  整组 `_safe_print(+BUILD_STRING+PRECALL/CALL)` 12 条指令蒸发（163 vs 153）。
  修复：`_generate_boolop_impl` 值语境「裸 Expr(BoolOp) 兜底」前新增封闭守卫
  `_v168_try_boolop_expr_group_tail`——merge 块以 keep-or-pop 收尾、块体无语句
  边界时，沿 fall-through 走到「CALL 之后的 POP_TOP」，把整条语句的线性指令窗
  交重建器（fold_boolop_keep_or_pop=True，与 v105 kwargs 续接/推导式元素窗同一
  开关），发射完整调用；完成块只登记指令粒度前缀（_register_prefix_emitted），
  块本身留给后续 if 继续取条件。

E2（守卫丢失）：循环尾 `if verbose:` 的测试与上一条 `_safe_print(t.name + ('/' if
  isdir else ''))` 的调用尾共处一块 @684 =
  [BINARY_OP, PRECALL, CALL, POP_TOP, LOAD_FAST verbose, POP_JUMP_FORWARD_IF_FALSE]。
  该块是 TernaryRegion@614 的 merge_block，`_ternary_host_call_prefix_span`
  把三元整体跨度归约成一条语句后，把尾段 [LOAD_FAST verbose, POP_JUMP] 当「剩余
  语句」交 `_build_statements_from_instructions` ⇒ 只发出裸 Expr `verbose`，
  POP_JUMP 丢失、两个 `if issym/islnk` 被降级成循环体兄弟。
  修复：`_r2156_tail_is_bounded_statements`（R21-56 消费判据：尾段不得含条件
  跳转、末条必须是语句边界）由「仅当使用了 R21-55c 异常边放宽」放开为对全部
  跨度生效；不命中 return None 退回既有非跨度路径（该块随后由循环体块派发正常
  发射 `_safe_print(...)` + `if verbose:`）。

用法
----
  python -I -X utf8 fix168.py          # 打补丁（幂等）
  python -I -X utf8 fix168.py --check  # 只检查当前状态
"""
import os
import py_compile
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')

# ---- 1) ----
A1 = """    def _generate_boolop_impl(self, region: BoolOpRegion, skip_store_targets: Set[str] = None) -> Optional[List[Dict[str, Any]]]:
"""

R1 = """    def _v168_try_boolop_expr_group_tail(self, region, op_chain, boolop_expr, results) -> bool:
        \"\"\"[v168-EXPRTAIL] 表达式语句内「链结果继续被格式化/拼接」的跨块续接。

        ①算法依据：No More Gotos 四原则 + 原则 1（块 = 前导语句 + 尾跳转）。
        CPython 3.11 把 `f(f"{a or b}/{c or d}")` 编译为：链 1 的 keep-or-pop
        落在「格式化当前操作数并开始链 2」的块上（该块既是链 1 的 merge，又是
        链 2 的 entry），链 2 的 keep-or-pop 落在「BUILD_STRING + PRECALL + CALL
        + POP_TOP」的语句完成块上。分析器按块边界把两条链各注册成一个
        BoolOpRegion（链 1 merge = 链 2 entry），两次归约都只覆盖「半条语句」：
        链 1 丢宿主调用（LOAD_GLOBAL）与格式化后缀，链 2 的 merge 块首的
        FORMAT_VALUE/BUILD_STRING 被后续 if 的条件提取当作前导丢弃 ⇒ 整条调用
        语句蒸发，只剩 `a or b` / `c` 两条裸 Expr。

        ②归约顺序：自底向上——本方法只在「BoolOpRegion 将以裸 Expr(BoolOp)
        发射」的那一刻介入（即既有归约已经失败），把该语句的线性指令窗（链首
        块起 → 语句完成点上的 POP_TOP）作为一个整体交重建器，keep-or-pop 由
        同一开关折叠为 BoolOp 操作数（[B237-V3R40] 推导式元素窗先例，
        _v105_try_kwarg_chain_continuation 的 kwargs 双链续接同源）。

        ③唯一归属判定（全结构事实，无名字/常量/偏移白名单）：
          - merge 块非噪声指令以值语境短路跳转收尾（链结果不是语句值）；
          - merge 块体内、链首块体内均无语句边界（赋值/返回/抛出/清理/弹栈）；
          - 沿 fall-through 行走 ≤8 块，完成块内出现「CALL 之后的 POP_TOP」；
          - 重建成功且结果不是原 boolop 本身。
        命中时：链上非完成块登记 generated/generated_offsets，完成块只登记
        指令粒度的已发射前缀（_register_prefix_emitted），块本身留给后续
        if/区域继续取条件；块集完全落在已消费集合内的兄弟区域一并登记
        _generated_regions（原则 4 父引用子入口）。任一守卫不满足即 return
        False，调用方按既有裸 Expr(BoolOp) 兜底（C3 逐位回退）。

        ④嵌套处理：窗内嵌套链由 keep-or-pop 折叠为一个 BoolOp 抽象节点，
        不拆散其内部块。
        ⑤入口引用语义：只返回 bool；语句由调用方 results 装配。
        ⑥反编译流程：_generate_boolop_impl 值语境「Expr(BoolOp) 兜底」之前的
        封闭守卫路径，排在 B56 RETURN 续接与 v105 kwargs 续接之后。
        \"\"\"
        _noise = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
        _mb = getattr(region, 'merge_block', None)
        if _mb is None or not op_chain:
            return False
        _mnn = [i for i in _mb.instructions if i.opname not in _noise]
        if not _mnn:
            return False
        # 守卫①：merge 块以值语境 keep-or-pop 收尾（链结果不是语句值）
        if (_mnn[-1].opname not in SHORT_CIRCUIT_JUMP_OPS
                or _mnn[-1].argval is None):
            return False
        # 守卫②：语句边界禁令（merge 块体 / 链首块体）
        _ban = ('STORE_', 'RETURN_', 'RAISE', 'RERAISE', 'POP_TOP', 'POP_EXCEPT',
                'PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'YIELD', 'SEND', 'SWAP',
                'COPY', 'DUP_TOP', 'FOR_ITER', 'SEND')
        _head = op_chain[0][0]
        _hnn = [i for i in _head.instructions if i.opname not in _noise]
        if not _hnn:
            return False
        for _i in _mnn[:-1]:
            if _i.opname.startswith(_ban) or _i.opname in _ban:
                return False
        for _i in _hnn[:-1]:
            if _i.opname.startswith(_ban) or _i.opname in _ban:
                return False
        _jump_ban = ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                     'JUMP_BACKWARD_NO_INTERRUPT')
        if _hnn[-1].opname in _jump_ban or _mnn[-1].opname in _jump_ban:
            return False
        # 守卫③：沿 fall-through 走到「CALL 之后的 POP_TOP」语句完成点
        _cur = _head
        _win = []
        _consumed = []
        _end_block = None
        _seen = set()
        for _step in range(8):
            if _cur is None or id(_cur) in _seen:
                return False
            _seen.add(id(_cur))
            _cn = [i for i in _cur.instructions if i.opname not in _noise]
            if not _cn:
                return False
            _pi = next((k for k, i in enumerate(_cn) if i.opname == 'POP_TOP'), None)
            if _pi is not None:
                if not any(i.opname in ('PRECALL', 'CALL', 'CALL_FUNCTION_EX')
                           for i in _cn[:_pi]):
                    return False
                _win.extend(_cn[:_pi + 1])
                _end_block = _cur
                break
            _win.extend(_cn)
            _consumed.append(_cur)
            _ln = _cn[-1]
            _jt = None
            if isinstance(_ln.argval, int):
                _jt = self.cfg.get_block_by_offset(_ln.argval)
            _nxt = None
            for _s in _cur.successors:
                if _s is not _jt:
                    _nxt = _s
                    break
            _cur = _nxt
        if _end_block is None or not _consumed:
            return False
        # 守卫④：线性窗重建（keep-or-pop 折叠）
        try:
            _expr = self.expr_reconstructor.reconstruct(
                list(_win), fold_boolop_keep_or_pop=True)
        except Exception:
            _expr = None
        if not isinstance(_expr, dict) or _expr.get('type') not in (
                'Call', 'JoinedStr', 'BinOp', 'Compare', 'BoolOp', 'IfExp',
                'Subscript', 'Starred', 'Tuple', 'List', 'Dict', 'Set'):
            return False
        if _expr == boolop_expr:
            return False
        # 记账：链上非完成块整体登记；完成块只登记指令粒度前缀
        _consumed_set = set(_consumed)
        for _b in _consumed:
            self.generated_blocks.add(_b)
            for _ins in getattr(_b, 'instructions', None) or []:
                _off = getattr(_ins, 'offset', None)
                if _off is not None:
                    self.generated_offsets.add(_off)
        _win_last_off = getattr(_win[-1], 'offset', None)
        if _win_last_off is not None:
            self._register_prefix_emitted(
                _end_block,
                [i for i in getattr(_end_block, 'instructions', None) or []
                 if getattr(i, 'offset', None) is not None
                 and i.offset <= _win_last_off])
        for _r in self.regions:
            if _r is region or id(_r) in self._generated_regions:
                continue
            _rb = set(getattr(_r, 'blocks', None) or [])
            if _rb and _rb <= _consumed_set:
                self._generated_regions.add(id(_r))
        self._generated_regions.add(id(region))
        results.append({'type': 'Expr', 'value': _expr})
        return True

    def _generate_boolop_impl(self, region: BoolOpRegion, skip_store_targets: Set[str] = None) -> Optional[List[Dict[str, Any]]]:
"""


# ---- 2) ----
A2 = """                        _b56_done = self._v105_try_kwarg_chain_continuation(
                            region, op_chain, boolop_expr, results)
                    if not _b56_done:
                        results.append({'type': 'Expr', 'value': boolop_expr})
"""

R2 = """                        _b56_done = self._v105_try_kwarg_chain_continuation(
                            region, op_chain, boolop_expr, results)
                    if not _b56_done and op_chain and region.merge_block is not None:
                        # [v168-EXPRTAIL] 表达式语句内跨块续接：链结果继续被
                        # FORMAT_VALUE/BUILD_STRING/宿主调用消费（如
                        # `_safe_print(f'{a or b}/{c or d}')`）。v105 只覆盖
                        # STORE 完成的赋值语句；表达式语句（POP_TOP 完成）此前
                        # 坍缩为裸 Expr(BoolOp)，宿主调用整组蒸发。
                        _b56_done = self._v168_try_boolop_expr_group_tail(
                            region, op_chain, boolop_expr, results)
                    if not _b56_done:
                        results.append({'type': 'Expr', 'value': boolop_expr})
"""


# ---- 3) ----
A3 = """        if _r2156_relaxed_used and tail_instrs:
            if not self._r2156_tail_is_bounded_statements(tail_instrs):
                return None
"""

R3 = """        # [v168-TAILGUARD] 消费判据（_r2156_tail_is_bounded_statements）从
        # 「仅依赖 R21-55c 异常边放宽的跨度」放开为对**全部**跨度生效：
        # 跨度闭合块的剩余尾段若含条件跳转（= 下一条 if/while 的测试前半段）或
        # 不以语句边界收尾，说明尾段不是自足语句 —— 此时把尾段当表达式发射会
        # 把 `if verbose:` 的 POP_JUMP 吞成裸 Expr `verbose`（TarFile.list 实测），
        # 而跨度已把该块整体登记为已生成 ⇒ 条件语句整体消失。不命中即 return
        # None，退回既有非跨度路径（C3：命中判据只读 opcode 族，无新增放宽）。
        if tail_instrs:
            if not self._r2156_tail_is_bounded_statements(tail_instrs):
                return None
"""


MARKER = '_v168_try_boolop_expr_group_tail'
ANCHORS = ((A1, R1), (A2, R2), (A3, R3))


def main():
    only_check = '--check' in sys.argv
    raw = open(TARGET, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig' if has_bom else 'utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = text.replace('\r\n', '\n')

    if MARKER in norm:
        print('[fix168] already applied (marker present) — no change')
        return 0

    for a, _r in ANCHORS:
        n = norm.count(a)
        if n != 1:
            print('[fix168] FAILED: anchor count=%d (expected 1): %r' % (n, a.strip()[:60]))
            return 2

    new_norm = norm
    for a, r in ANCHORS:
        new_norm = new_norm.replace(a, r)
    if only_check:
        print('[fix168] check: patchable (all 3 anchors count=1), not applied')
        return 0

    out = new_norm.replace('\n', nl).encode('utf-8')
    expect = raw
    for a, r in ANCHORS:
        expect = expect.replace(a.replace('\n', nl).encode('utf-8'),
                                r.replace('\n', nl).encode('utf-8'))
    if out != expect:
        print('[fix168] FAILED: byte-level round-trip mismatch')
        return 3
    inserted = sum(r.count('\n') - a.count('\n') for a, r in ANCHORS)
    if out.count(nl.encode()) != raw.count(nl.encode()) + inserted:
        print('[fix168] FAILED: line-count accounting mismatch')
        return 4

    tmpdir = tempfile.mkdtemp(prefix='fix168_')
    tmp_py = os.path.join(tmpdir, 'patched.py')
    with open(tmp_py, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(tmp_py, cfile=tmp_py + 'c', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        print('[fix168] FAILED: patched source does not compile: %s' % exc)
        return 5

    with open(TARGET, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(TARGET, cfile=tmp_py + 'c2', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        with open(TARGET, 'wb') as f:
            f.write(raw)
        print('[fix168] ROLLED BACK: target does not compile: %s' % exc)
        return 6

    print('[fix168] applied: +%d lines, py_compile OK (%s%s)' % (
        inserted, TARGET, ', BOM preserved' if has_bom else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
