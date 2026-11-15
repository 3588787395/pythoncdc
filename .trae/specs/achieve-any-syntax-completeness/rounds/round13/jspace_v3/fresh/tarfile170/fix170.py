#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r170 修 tarfile `_Stream._init_read_gz`（族 F：短路链出环 + 循环后 if 去嵌套）。

两面同轮（缺一不可；r167 的 150/151 边际已在本轮复验）
------------------------------------------------------
F1「形态面」（`_loop_build_if_with_exit_branches`）：
  `if not s or s == NUL: break` 的 3.11 字节码 = 第一操作数取反后的
  POP_JUMP_IF_FALSE + 第二操作数比较的 POP_JUMP_IF_FALSE，且第二操作数块的
  落空边直达同一 break 块。旧路径按「then=落空块 / else=跳转块」逐臂归约，
  落空块自身又含一条条件跳转 ⇒ 被 _generate_block_statements 发射成内层 if，
  得到等价但多指令的 `if s: if s == NUL: break / else: break`（内层 if 的
  空 else 物化成额外 JUMP_FORWARD，重编译多 2 条跳转；第二循环的 break 在
  旧路径里还会丢成 pass）。修复 [v170-LOOP-OR-CHAIN]：识别「落空块末条实指令
  是条件跳转、两个后继一个是该 break 块、另一个是循环回边、跳转前是纯表达式
  段」，把两跳各自归一为操作数，合成 BoolOp(or, [第一操作数, 第二操作数]) 的
  单一 `if ...: Break`。
  宿主门（红线 f2 锁）：仅当本循环的父区域是 IfRegion 且其 merge_block 正是
  本循环的 break 落点（r169 `_v169_post_loop_parent_if` 的同一结构事实）时
  生效——f2 的裸 while 无 IfRegion 宿主，逐字节不变。

F2「去嵌套面」（`generate()` 的包含判定 + r169 已做的收集/登记跳过）：
  循环所在 IfRegion 的 merge_block 恰是循环的 break 落点，以该落点为 entry 的
  IfRegion 在包含判定里会被「entry ∈ LoopRegion.blocks」判成嵌套子区域而滤出
  top_level_regions。r169 已让循环侧不收集、不登记该落点（交外层序列发射），
  但外层序列拿不到这个区域时，整条 if 守卫与体内 while 会静默蒸发（tarfile
  _init_read_gz 实测：`if flag & 16` / `if flag & 2` 的守卫与 while 整段消失，
  只剩循环后的裸语句）。修复 [v170-POSTLOOP-REGION]：同一条结构判据下不判
  contained，保留为顶级区域，由 generate() 顶级序列按 entry 偏移在 If 之后
  发射（= 循环所在 if 的兄弟位置）。

读数（本轮实测）
----------------
  tarfile 154/160 → **155/160**；`_Stream._init_read_gz` EQUAL（失败 5 项 =
  `_Stream._read` / `_FileInFile.read` / `add` / `next` / `main`）。
  四语料 request 194/194、difflib 62/62、cookiejar 91/105、subprocess 69/78，
  产物与 r169 逐字节 SAME。红线 38/38 SAME（含 f2/fc2）。458 电池 9 TEXT-DIFF
  （v111 三 + E161 六）全 BYTE-EQUAL、C7_skipedge TEXT-SAME。

用法
----
  python -I -X utf8 fix170.py          # 打补丁（幂等）
  python -I -X utf8 fix170.py --check  # 只检查当前状态
"""
import os
import py_compile
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')

MARKERS = ('v170-POSTLOOP-REGION', 'v170-LOOP-OR-CHAIN')

A1 = '            for other in self.regions:\n                if other is not r and r.entry and r.entry in other.blocks:\n                    if other.region_type != RegionType.BASIC:\n                        if other.parent is r:\n                            continue\n                        if len(r.blocks) > len(other.blocks):\n                            continue'

R1 = "            for other in self.regions:\n                if other is not r and r.entry and r.entry in other.blocks:\n                    if other.region_type != RegionType.BASIC:\n                        if other.parent is r:\n                            continue\n                        # [v170-POSTLOOP-REGION] 与 _v169_post_loop_parent_if 同一\n                        # 结构事实的发射侧收口：循环的 break 落点恰是宿主 IfRegion\n                        # 的 merge 时，以该落点为 entry 的 IfRegion 在包含判定里会\n                        # 被「entry ∈ LoopRegion.blocks」判成嵌套子区域而滤出\n                        # top_level_regions。r169 已让循环侧不收集、不登记该落点\n                        # （交外层序列发射），但外层序列若拿不到这个区域，整条 if\n                        # 守卫与体内语句会静默蒸发（f3 / tarfile._init_read_gz\n                        # 实测：`if flag & 16` / `if flag & 2` 的守卫与 while 整段\n                        # 消失，只剩循环后的裸语句）。判据只读同层结构身份：该\n                        # IfRegion 的 entry 是此 LoopRegion 的 break 落点，且是该\n                        # 循环宿主 IfRegion 的汇合块（复用同一谓词）。归约方式——\n                        # 不判 contained，保留为顶级区域，由 generate() 的顶级序列\n                        # 按 entry 偏移在 If 之后发射（= 循环所在 if 的兄弟位置）。\n                        # C 条款：[C1] 只读 break_blocks/parent/汇合块/entry 身份；\n                        # [C2] 命中才改变归属，未命中逐位保持原包含判定（C3）。\n                        if (isinstance(other, LoopRegion) and isinstance(r, IfRegion)\n                                and r.entry is not None\n                                and r.entry in (getattr(other, 'break_blocks', None) or ())\n                                and self._v169_post_loop_parent_if(other, r.entry) is not None):\n                            continue\n                        if len(r.blocks) > len(other.blocks):\n                            continue"

A2 = "        _then_succ = _fall_through\n        _else_succ = _jump_block\n        _negate = not _is_if_false\n        _then_stmts = _r68_branch(_then_succ) or [{'type': 'Pass'}]"

R2 = "        # [v170-LOOP-OR-CHAIN] 短路链出环条件（`if not s or s == NUL: break`）：\n        # 3.11 把「第一操作数取反 + 第二操作数比较」融合成两条 POP_JUMP_IF_FALSE，\n        # 且第二操作数块的落空边直达同一 break 块。旧路径按「then=落空块、\n        # else=跳转块」逐臂归约：落空块自身又含一条条件跳转，于是被\n        # _generate_block_statements 发射成内层 if，得到等价但多指令的\n        # `if s: if s == NUL: break / else: break`（内层 if 的空 else 被物化成\n        # 额外 JUMP_FORWARD，重编译多 2 条跳转）。\n        # 识别条件（全部只读本调用点已有形参与本块自身指令/后继，无名字/偏移\n        # 阈值）：①落空块不是出口、跳转块是 break（∈ _block_succ_break，角色\n        # BREAK/PURE_BREAK）；②落空块末条实指令是条件跳转，其两个后继一个是\n        # 该 break 块、另一个是循环回边（非出口）；③落空块跳转前的指令是纯\n        # 表达式段（无 STORE_*/POP_TOP 边界），可重建为操作数表达式。\n        # 归约方式：把两跳的「谁导致 break」各自归一为操作数，合成\n        # BoolOp(or, [第一操作数, 第二操作数]) 的单一 `if ...: Break`。\n        # 宿主门（红线 f2 锁）：仅当本循环的父区域是 IfRegion 且其汇合块正是\n        # 本循环的 break 落点（r169 的 _v169_post_loop_parent_if 同一结构事实）\n        # 时生效——f2 的裸 while 无 IfRegion 宿主，逐字节不变。\n        # AST 映射：If(test=BoolOp(or), body=[Break])，两臂块登记 generated。\n        # C 条款：[C1] 只读本块指令/后继/角色 + _current_loop 父链；[C2] 命中\n        # 才改发射形态，未命中逐位沿用 `_r68_branch` 旧路径（C3）。\n        _v170_lc = getattr(self, '_current_loop', None)\n        _v170_par = getattr(_v170_lc, 'parent', None)\n        _v170_lc_join = getattr(_v170_par, 'merge_block', None)\n        _v170_hosted = (\n            isinstance(_v170_lc, LoopRegion) and isinstance(_v170_par, IfRegion)\n            and _v170_lc_join is not None\n            and any(_vb is _v170_lc_join for _vb in (getattr(_v170_lc, 'break_blocks', None) or ())))\n        if (_v170_hosted and _fall_through is not None and _jump_block is not None\n                and _jump_block in _block_succ_break\n                and self.region_analyzer.get_block_role(_jump_block) in (BlockRole.BREAK, BlockRole.PURE_BREAK)):\n            _v170_cj = None\n            for _v170_ins in reversed(_fall_through.instructions):\n                if _v170_ins.opname in NOISE_OPS:\n                    continue\n                if _v170_ins.opname in CONDITIONAL_JUMP_OPS:\n                    _v170_cj = _v170_ins\n                break\n            _v170_succ = list(_fall_through.successors or [])\n            _v170_other = [_s for _s in _v170_succ if _s is not _jump_block]\n            _v170_other_ok = False\n            if len(_v170_other) == 1 and _v170_other[0] not in _exit_succs:\n                _v170_o = _v170_other[0]\n                _v170_otl = _v170_o.get_last_instruction()\n                _v170_other_ok = (\n                    self.region_analyzer.get_block_role(_v170_o) in (\n                        BlockRole.CONTINUE, BlockRole.PURE_CONTINUE, BlockRole.LOOP_BACK_EDGE)\n                    or (_v170_otl is not None\n                        and _v170_otl.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')))\n            if (_v170_cj is not None and _v170_cj.argval is not None\n                    and _jump_block in _v170_succ and _v170_other_ok):\n                _v170_pre = []\n                for _v170_ins in _fall_through.instructions:\n                    if _v170_ins is _v170_cj:\n                        break\n                    if _v170_ins.opname in NOISE_OPS or _v170_ins.opname in PURE_JUMP_OPS:\n                        continue\n                    _v170_pre.append(_v170_ins)\n                _v170_clean = bool(_v170_pre) and not any(\n                    _v170_ins.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',\n                                         'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR', 'POP_TOP')\n                    for _v170_ins in _v170_pre)\n                _v170_ft_expr = (self.expr_reconstructor.reconstruct(_v170_pre)\n                                 if _v170_clean else None)\n                if _v170_ft_expr:\n                    # 外层操作数：跳转块（break）在条件为假（IF_FALSE）时执行 ⇒ `not C`；\n                    # IF_TRUE 时执行 ⇒ `C`。\n                    _v170_first = (_negate_expr(_expr) if _is_if_false else _expr)\n                    # 内层操作数：落空块的条件跳转 —— 落空边到 break ⇒ 测试为真\n                    # 时 break（IF_FALSE 落空 = 真，IF_TRUE 落空 = 假）；跳转边到\n                    # break 取反。\n                    _v170_ft_jt = 'IF_TRUE' in _v170_cj.opname\n                    _v170_jumps_to_break = (_v170_cj.argval == _jump_block.start_offset)\n                    if _v170_jumps_to_break:\n                        _v170_second = _v170_ft_expr if _v170_ft_jt else _negate_expr(_v170_ft_expr)\n                    else:\n                        _v170_second = _negate_expr(_v170_ft_expr) if _v170_ft_jt else _v170_ft_expr\n                    _hdr_stmts.append({'type': 'If',\n                                       'test': {'type': 'BoolOp', 'op': 'or',\n                                                'values': [_v170_first, _v170_second]},\n                                       'body': [{'type': 'Break'}]})\n                    for _v170_b in (_fall_through, _jump_block):\n                        self.generated_blocks.add(_v170_b)\n                        self.generated_offsets.add(_v170_b.start_offset)\n                    return\n        _then_succ = _fall_through\n        _else_succ = _jump_block\n        _negate = not _is_if_false\n        _then_stmts = _r68_branch(_then_succ) or [{'type': 'Pass'}]"

ANCHORS = ((A1, R1), (A2, R2))


def main():
    only_check = '--check' in sys.argv
    raw = open(TARGET, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig' if has_bom else 'utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = text.replace('\r\n', '\n')

    if all(m in norm for m in MARKERS):
        print('[fix170] already applied (markers present) — no change')
        return 0
    if any(m in norm for m in MARKERS):
        print('[fix170] FAILED: partial application (one marker present)')
        return 6

    for a, _r in ANCHORS:
        n = norm.count(a)
        if n != 1:
            print('[fix170] FAILED: anchor count=%d (expected 1): %r' % (n, a.strip()[:60]))
            return 2

    new_norm = norm
    for a, r in ANCHORS:
        new_norm = new_norm.replace(a, r)
    if only_check:
        print('[fix170] check: patchable (all %d anchors count=1), not applied' % len(ANCHORS))
        return 0

    out = new_norm.replace('\n', nl).encode('utf-8')
    expect = raw
    for a, r in ANCHORS:
        expect = expect.replace(a.replace('\n', nl).encode('utf-8'),
                                r.replace('\n', nl).encode('utf-8'))
    if out != expect:
        print('[fix170] FAILED: byte-level round-trip mismatch')
        return 3
    inserted = sum(r.count('\n') - a.count('\n') for a, r in ANCHORS)
    if out.count(nl.encode()) != raw.count(nl.encode()) + inserted:
        print('[fix170] FAILED: line-count accounting mismatch')
        return 4

    tmpdir = tempfile.mkdtemp(prefix='fix170_')
    tmp_py = os.path.join(tmpdir, 'patched.py')
    with open(tmp_py, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(tmp_py, cfile=tmp_py + 'c', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        print('[fix170] FAILED: patched source does not compile: %s' % exc)
        return 5

    with open(TARGET, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(TARGET, cfile=tmp_py + 'c2', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        with open(TARGET, 'wb') as f:
            f.write(raw)
        print('[fix170] FAILED: on-disk compile failed, rolled back: %s' % exc)
        return 5

    print('[fix170] applied: %d anchors, +%d lines, %d bytes' % (
        len(ANCHORS), inserted, len(out) - len(raw)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
