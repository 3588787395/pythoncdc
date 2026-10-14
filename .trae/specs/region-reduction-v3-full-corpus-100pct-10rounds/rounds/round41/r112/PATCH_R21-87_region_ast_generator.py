# -*- coding: utf-8 -*-
r"""PATCH_R21-87_region_ast_generator.py — [R21-86] `59a405837c22a4cb` -> [R21-87] candidate.

FROM:  D:/Temp/r112/backup/gen_r2186_59a405837c22a4cb.py   (sha16 59a405837c22a4cb, the
       campaign's best-known arm generator = [R21-86], itself built from the landed bytes
       566ff5c502276e48 by rounds/round41/r111/PATCH_R21-86_region_ast_generator.py)
TO:    D:/Temp/r112/core/cfg/region_ast_generator.py        (sha16 printed at the end)

This patch is a pure ADDITIVE two-anchor edit of [R21-86] (it does not touch any [R21-86]
line), is IDEMPOTENT (it detects its own insertion and exits without rewriting), and uses
ABSOLUTE paths only.  File invariants asserted after writing: UTF-8 BOM present, 100 % CRLF,
zero bare LF, zero "\r\r\n", `python -X utf8 -m py_compile` clean.

Edit 1 (new resident-scale sibling): insert `_r2187_and_prefix_or_tail` immediately before
  `_r4701_and_lift_or_tail` — the positive-polarity sibling of that landed ruler, same family,
  same evidence class (jump polarity + region/block data only).
Edit 2 (call site): invoke it in `_if_generate_normal` right after the `inline_boolop_chains`
  / `_discover_predicate_and_chain` condition assembly and before the arm walk, i.e. at
  identification time, before the statement is emitted.
"""
import hashlib
import os
import subprocess
import sys

SRC = 'D:/Temp/r112/backup/gen_r2186_59a405837c22a4cb.py'
DST = 'D:/Temp/r112/core/cfg/region_ast_generator.py'
EXPECT_SRC = '59a405837c22a4cb'

ANCHOR_A = "    def _r4701_and_lift_or_tail(self, region, cond_block, expr):"

ANCHOR_B = ("                finally:\r\n"
            "                    _cpg.discard(id(region))\r\n"
            "        self.generated_blocks.add(cond_block)")

METHOD = """    def _r2187_and_prefix_or_tail(self, region, cond_block, condition):
        \"\"\"[R21-87] 正极性 and 前缀腿 + or 尾腿 ⇒ 就地发射单条 `(A and B) or C` 测试。

        CPython 把 `if (A and B) or C: <arm>`（语句之后顺接 E）编译成三条短路腿：
            A; POP_JUMP_IF_FALSE -> T        (A 假时不是跳过语句，而是直接求值尾腿 C)
            B (链式比较跨多块); POP_JUMP_IF_TRUE -> arm，落空经连接块 -> T
            T: C; POP_JUMP_IF_FALSE -> E，为真直落 arm
        区域归约把三条腿拆成三个 IfRegion：R(cond=A, merge=T, else=[])、
        Mr(cond=B)、Tr(entry=T, cond=T)。逐层发射即得 `if A: if B or C: <arm>`，
        多出一层脚手架、并把 arm 之后的下一条 `if` 误并成本语句的 elif 臂
        （realtime_event_source::clock_worker 实测 ours=+8 行、jsites=+2、
        indeg-equal=False）。

        判据（六条同时成立，全部是本层结构事实：跳转极性 + 区域/块数据；
        不读函数名/文件名/绝对偏移键/计数器/阈值/幅度比较）：
          (1) cond_block 末跳为 IF_FALSE（非 NONE_CHECK）-> T，T is region.merge_block，
              region.else_blocks 为空 —— 外层腿为正极性单腿；
          (2) T 自身末跳亦为 IF_FALSE -> E（E != T，E 即 region 内不存在臂），
              T 的另一后继中**恰有一个**落在 region.then_blocks 里 —— 它就是臂入口 arm，
              故 T 是本条测试的 or 尾腿而非语句汇合点；
          (3) cond_block 的非 T 后继里**恰有一个**位于 (cond_block, T) 之间且是某
              IfRegion Mr 的 entry 且 Mr.condition_block is Mr.entry —— 中间 and 腿；
          (4) Mr 腿的最后一个测试块（M 连同 chained_compare_blocks 中偏移最大者）末跳
              IF_TRUE -> arm —— and 腿真出口即本语句臂；
          (5) T 的某个前驱位于 [Mr.entry, T) 且不是 cond_block —— and 腿落空交回尾腿；
          (6) 三支表达式均可重建：A 取已装配的 condition（缺失时按同一指令过滤尺
              从 cond_block 重建），B 走链式比较已存尺 _build_chained_compare_from_region_data
              （无链式比较时按同一尺重建），C 由 T 除去末跳的指令重建。
        归约方式：测试 = BoolOp(or, [BoolOp(and, [A, B]), C])；region.then_blocks 收窄为
          [arm, E) 偏移区间内的原成员（= 本语句的臂，原则 4：臂内嵌套区域仍作抽象节点
          由既有子区域分发），region.merge_block 改声明为 E；三条腿的测试块（Mr.entry、
          其 chained_compare_blocks、T）与其间的纯连接块（指令类仅
          POP_TOP/NOP/RESUME/CACHE/JUMP_FORWARD/EXTENDED_ARG）标记 generated_blocks /
          generated_offsets —— 与已落地 _r4701_and_lift_or_tail 的交还手法同一族（原则 2：
          腿块唯一发射者就是本语句）。臂区间（含 [R21-86] 释放台账所要找回的那一段）
          一律不标记，故与 [R21-86] 正交。
        AST 映射：If(test=BoolOp(or,[BoolOp(and,[A,B]),C]), body=<arm 语句序列>)，
          在本区域原来的序列位置单条发射：无事后文本修补、无已发射语句重排、
          无 un-mark-and-reprint、单向数据流。
        任一合取不成立 ⇒ 返回 None，走既有路径，产物逐字节不变。
        \"\"\"
        try:
            if region is None or cond_block is None:
                return None
            if getattr(region, 'else_blocks', None):
                return None
            _tb = getattr(region, 'then_blocks', None)
            if not _tb:
                return None
            _li = cond_block.get_last_instruction()
            if (_li is None or getattr(_li, 'argval', None) is None
                    or 'IF_FALSE' not in _li.opname
                    or _li.opname in NONE_CHECK_OPS):
                return None
            _t_off = _li.argval
            _t = self.cfg.get_block_by_offset(_t_off)
            if _t is None or _t is not getattr(region, 'merge_block', None):
                return None
            if _t is cond_block or _t_off <= cond_block.start_offset:
                return None
            _ti = _t.get_last_instruction()
            if (_ti is None or getattr(_ti, 'argval', None) is None
                    or 'IF_FALSE' not in _ti.opname
                    or _ti.opname in NONE_CHECK_OPS):
                return None
            _e_off = _ti.argval
            if _e_off == _t_off:
                return None
            _e = self.cfg.get_block_by_offset(_e_off)
            if _e is None:
                return None
            _arm_c = [s for s in (_t.successors or [])
                      if s.start_offset != _e_off and s in _tb]
            if len(_arm_c) != 1:
                return None
            _arm = _arm_c[0]
            _m_c = [s for s in (cond_block.successors or [])
                    if s.start_offset != _t_off
                    and cond_block.start_offset < s.start_offset < _t_off]
            _regions = self.region_analyzer.regions
            _mr = None
            _tr = None
            for _r in _regions:
                if not isinstance(_r, IfRegion):
                    continue
                if _r.entry is _t:
                    _tr = _r
                for _s in _m_c:
                    if _r.entry is _s and getattr(_r, 'condition_block', None) is _s:
                        _mr = _r
            if _mr is None or _tr is None:
                return None
            if getattr(_tr, 'condition_block', None) is not _t:
                return None
            if len(_m_c) != 1:
                return None
            _m = _m_c[0]
            _ccb = list(getattr(_mr, 'chained_compare_blocks', None) or [])
            _leg = [_m] + _ccb
            _lt = max(_leg, key=lambda b: b.start_offset)
            _lti = _lt.get_last_instruction()
            if (_lti is None or getattr(_lti, 'argval', None) is None
                    or 'IF_TRUE' not in _lti.opname
                    or _lti.opname in NONE_CHECK_OPS
                    or _lti.argval != _arm.start_offset):
                return None
            if not any(p is not cond_block and p.start_offset >= _m.start_offset
                       and p.start_offset < _t_off
                       for p in (_t.predecessors or [])):
                return None
            _skip_ops = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
            _a = condition
            if _a is None:
                _a_instrs = [i for i in cond_block.instructions
                             if i.opname not in _skip_ops and i is not _li]
                _a = self.expr_reconstructor.reconstruct(_a_instrs) if _a_instrs else None
            if _a is None:
                return None
            if _ccb and getattr(_mr, 'chained_compare_ops', None):
                _b = self._build_chained_compare_from_region_data(_mr)
            else:
                _b_instrs = [i for i in _lt.instructions
                             if i.opname not in _skip_ops and i is not _lti]
                _b = self.expr_reconstructor.reconstruct(_b_instrs) if _b_instrs else None
            if _b is None:
                return None
            _c_instrs = [i for i in _t.instructions
                         if i.opname not in _skip_ops and i is not _ti]
            _c = self.expr_reconstructor.reconstruct(_c_instrs) if _c_instrs else None
            if _c is None:
                return None
            _cleanup_ops = ('POP_TOP', 'NOP', 'RESUME', 'CACHE', 'JUMP_FORWARD',
                            'EXTENDED_ARG')
            _mark = [_m, _t, _lt] + _ccb
            for _pb in (list(getattr(region, 'blocks', None) or [])
                        + list(getattr(_mr, 'blocks', None) or [])):
                if _pb is None or _pb is _arm or _pb is _e:
                    continue
                if not (_m.start_offset <= _pb.start_offset < _t_off):
                    continue
                if all(i.opname in _cleanup_ops for i in _pb.instructions):
                    _mark.append(_pb)
            _arm_blocks = sorted((b for b in _tb
                                   if _arm.start_offset <= b.start_offset < _e_off),
                                  key=lambda b: b.start_offset)
            if _arm not in _arm_blocks:
                return None
            if any(_ob not in set(_arm_blocks) and _ob not in set(_mark)
                   for _ob in _tb):
                return None
            _seen = set()
            for _mb in _mark:
                if _mb in _seen:
                    continue
                _seen.add(_mb)
                self.generated_blocks.add(_mb)
                self.generated_offsets.add(_mb.start_offset)
            region.then_blocks = _arm_blocks
            region.merge_block = _e
            _and_expr = {'type': 'BoolOp', 'op': 'and', 'values': [_a, _b]}
            _or_expr = {'type': 'BoolOp', 'op': 'or', 'values': [_and_expr, _c]}
            return self._convert_lambda_function_objects(_or_expr)
        except Exception:
            return None

"""

CALL = ("                finally:\r\n"
        "                    _cpg.discard(id(region))\r\n"
        "        # [R21-87] 正极性 `(A and B) or C` 短路线：装配完 condition 之后、在臂\r\n"
        "        # 序列分发之前，按本层结构事实就地折叠（判据见 _r2187_and_prefix_or_tail）。\r\n"
        "        # 不成立时返回 None ⇒ 既有路径逐字节不变。\r\n"
        "        _r2187_test = self._r2187_and_prefix_or_tail(region, cond_block, condition)\r\n"
        "        if _r2187_test is not None:\r\n"
        "            condition = _r2187_test\r\n"
        "        self.generated_blocks.add(cond_block)")


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main():
    assert os.path.isabs(SRC) and os.path.isabs(DST), 'absolute paths required'
    raw = open(SRC, 'rb').read()
    assert raw.startswith(b'\xef\xbb\xbf'), 'source has no BOM'
    assert h16(SRC) == EXPECT_SRC, 'base is not [R21-86]: %s' % h16(SRC)
    src = raw.decode('utf-8-sig')
    assert '\n' not in src.replace('\r\n', ''), 'source contains bare LF'
    already = ('_r2187_and_prefix_or_tail' in src)
    if already:
        print('[patch] anchor text already present -> idempotent no-op (re-copy only)')
    else:
        assert src.count(ANCHOR_A) == 1, 'anchor A count=%d' % src.count(ANCHOR_A)
        assert src.count(ANCHOR_B.replace('\r\n', '\n')) == 1 or src.count(ANCHOR_B) == 1, 'anchor B not unique'
        if ANCHOR_B in src:
            src = src.replace(ANCHOR_B, CALL, 1)
        else:
            src = src.replace(ANCHOR_B.replace('\r\n', '\n'),
                              CALL.replace('\r\n', '\n'), 1)
        src = src.replace(ANCHOR_A, METHOD + ANCHOR_A, 1)
    out = b'\xef\xbb\xbf' + src.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
    assert b'\r\r\n' not in out, 'CR CR LF introduced'
    body = out.decode('utf-8-sig')
    assert '\n' not in body.replace('\r\n', ''), 'bare LF introduced'
    assert body.count('\r\n') == len(body.split('\n')) - 1, 'not 100%% CRLF'
    open(DST, 'wb').write(out)
    r = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'py_compile', DST],
                       capture_output=True)
    print('[patch] py_compile rc=%d %s' % (r.returncode,
                                           (r.stderr or b'').decode('utf-8', 'replace')[:300]))
    assert r.returncode == 0
    print('[patch] bytes=%d bom=%s sha16=%s -> %s' % (
        len(out), out.startswith(b'\xef\xbb\xbf'), h16(DST), DST))
    assert r.returncode == 0 and os.path.getsize(DST) > 3_000_000


main()
