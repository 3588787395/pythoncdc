#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r167 修 tarfile「终结符 if / 短路第二操作数块被当作 else 臂」族（B+F 同源）。

缺陷（实证：D:/temp/opencode/cl_layout/r167/work/dbg_all.txt）
--------------------------------------------------------------
条件块的「跳转目标」被无条件当作 else 臂入口，缺少「目标块是本臂汇合点」判据：

  * `_Stream.__init__`（except 臂）：`try: if comptype=='gz': ... except: if not
    self._extfileobj: close(); self.closed = True; raise` —— 守卫 `if not ext` 的
    跳转目标（= `closed = True; raise` 块）同时是 then 臂（`close()` 块）的自然
    后继，是汇合点，却被当成 else 臂：产物 `if not ext: close() else: closed =
    True; raise`，真臂尾被注入 POP_EXCEPT/return None（+3 指令，异常表 DIFF）。
  * `_Stream._read` / `_Stream._init_read_gz` 同源（另见 BLOCKER_167.txt 记录）。

判据（本补丁只加一处判据 + 两处调用点）
--------------------------------------
新增 `_cjb_target_is_arm_join(block, cond_instr, then_entry, else_entry)`：
  条件跳转是前向条件跳转 ∧ 两臂入口互异 ∧ **跳转目标 ∈ then 臂入口的后继集**
  ⇒ 跳转目标是 then 臂的汇合点（if 之后的语句入口），不是 else 臂入口。
只读块后继集与跳转 opcode（I.4 白名单），不读名字/偏移/输入值；不命中时两处调用
点逐字节沿用原行为（C3）。

两处调用点（同一谓词，防漂移）：
  1) `_generate_handler_body_statements`：命中时把该「else 臂」语句作为 if 之后的
     兄弟语句发射（`stmts.extend`），不写 `if_stmt['orelse']`；
  2) `_generate_block_statements_body` 的 CJB 段：命中时 `orelse=None`，同一批语句
     追加在 If 节点之后。

用法
----
  python -I -X utf8 fix167.py          # 打补丁（幂等）
  python -I -X utf8 fix167.py --check  # 只检查当前状态
"""
import os
import py_compile
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')

# ---- 1) 新增判据方法（插在 _generate_handler_body_statements 定义之前） ----
A1 = """    def _generate_handler_body_statements(self, block: BasicBlock) -> List[Dict[str, Any]]:
        \"\"\"_generate_handler_body_statements — except handler / finally 副本体单块语句发射。
"""

R1 = """    def _cjb_target_is_arm_join(self, block: BasicBlock, cond_instr,
                                 then_entry, else_entry) -> bool:
        \"\"\"_cjb_target_is_arm_join — 条件跳转目标块是否为 then 臂汇合点判定。

        ①算法依据：区域归约算法原则 1（块 = 前导语句 + 尾跳转）＋原则 2（每块唯一
        归属）——CPython 3.11 对「无 else 的 if」把条件跳转直接指向 if 之后的第一条
        语句（= 汇合点），该块同时是 then 臂末块的自然后继；源码里带 else 的 if 中，
        条件跳转指向 else 臂入口，而 else 臂入口不是 then 臂任何块的后继（then 臂
        末块以无条件跳转越过 else 臂落到汇合点）。
        ②归约顺序：只读调用点已算好的四个身份（条件块 / 条件跳转指令 / 两臂入口
        块），不遍历、不缓存、不新增 self 状态。
        ③唯一归属判定：命中（跳转目标 ∈ then 臂入口的后继集）时，跳转目标是 then
        臂的汇合点（if 之后的语句入口），不是 else 臂入口 —— 该批语句归「if 之后的
        兄弟语句」发射，不写 orelse；不命中时调用方原路径逐字节不变（C3）。
        ④嵌套处理：不递归，只回答「是不是汇合点」；臂块的生成与认领仍由调用方负责。
        ⑤入口引用语义：返回 bool；两臂入口块的身份始终由调用方持有。
        ⑥反编译流程：条件块装配（CJB 段）与 except / finally 体装配两处共用本判据，
        同一结构事实只写一份，避免两处判据漂移。

        输入契约:
          - block: 条件块本身（只做空值否证）
          - cond_instr: 该块内的条件跳转指令（只读 opname，判定前向条件跳转）
          - then_entry / else_entry: 调用点已判定的两臂入口块

        字节码一致性约束:
          - 仅前向条件跳转参与（handler 体装配只处理前向条件跳转，两处口径一致）
          - 判据只读块后继集与跳转 opcode（I.4 白名单），不读名字 / 偏移 / 输入值
        \"\"\"
        if block is None or cond_instr is None:
            return False
        if then_entry is None or else_entry is None or then_entry is else_entry:
            return False
        if cond_instr.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
            return False
        if else_entry not in then_entry.successors:
            return False
        # [r167-ARMJOIN-NARROW] then 臂入口自身必须不是**任何**跳转／终结指令
        # 收尾的块（纯落空块）：此时它的非异常后继只能是落空边，跳转目标 ∈ 后继集
        # 就等价于「目标 = 臂尾之后的落空块」。反例（V122::C7_skipedge）：嵌套
        # 短路链里 then 臂入口本身以 POP_JUMP_FORWARD_IF_* 收尾，跳转目标是它的
        # 两个条件后继之一（共享 return sink），拍平会把 else: return 1 变成
        # 同级 return（语义变）。判据只读末指令 opcode（I.4 白名单）。
        _last_i = then_entry.get_last_instruction()
        if _last_i is None:
            return False
        if (_last_i.opname in FORWARD_JUMP_OPS
                or _last_i.opname in BACKWARD_JUMP_OPS
                or _last_i.opname in FORWARD_CONDITIONAL_JUMP_OPS
                or _last_i.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                or _last_i.opname in NONE_CHECK_OPS
                or _last_i.opname in SHORT_CIRCUIT_JUMP_OPS):
            return False
        return True

""" + A1

# ---- 2) handler 体装配调用点 ----
A2 = """                        if_stmt = {
                            'type': 'If',
                            'test': cond_expr,
                            'body': then_stmts if then_stmts else [{'type': 'Pass'}],
                        }
                        if else_stmts:
"""

R2 = """                        if_stmt = {
                            'type': 'If',
                            'test': cond_expr,
                            'body': then_stmts if then_stmts else [{'type': 'Pass'}],
                        }
                        # [r167-ARMJOIN] 区域归约算法原则 1／2：守卫 if 的跳转目标
                        # 若是 then 臂的自然后继（= 本臂汇合点，源码里的 if 之后
                        # 语句），它不是 else 臂入口。把它写成 orelse 会让真臂尾
                        # 被注入 POP_EXCEPT + return None，并把 handler 的清理指令
                        # 抢进 arm（_Stream.__init__ 异常表 DIFF 即此）。命中时该批
                        # 语句作为 if 之后的兄弟语句发射（每块唯一归属不变：块已在
                        # 上面认领进 generated_blocks）。判据见 _cjb_target_is_arm_join，
                        # 不命中逐字节回退（C3）。
                        if (else_stmts
                                and self._cjb_target_is_arm_join(
                                    block, instr, _then_succ, target_block)):
                            stmts.append(if_stmt)
                            stmts.extend(else_stmts)
                            stmt_instrs = []
                            continue
                        if else_stmts:
"""

# ---- 3) CJB 段调用点（采集侧标记） ----
A3 = """                _cjb_else_stmts = []
                for _eb in _cjb_else_blocks:
"""

R3 = """                # [r167-ARMJOIN] 与 handler 体装配同一判据（_cjb_target_is_arm_join）：
                # 跳转目标是 then 臂的汇合点时，else 入口不是 else 臂 —— 该批语句
                # 作为 If 之后的兄弟语句发射，orelse 省略。不命中时下游路径逐字节
                # 不变（_cjb_else_is_join 恒 False）。
                _cjb_else_is_join = self._cjb_target_is_arm_join(
                    block, _cond_jump_bs, _cjb_then_entry, _cjb_else_entry)
                _cjb_else_stmts = []
                for _eb in _cjb_else_blocks:
"""

# ---- 4) CJB 段发射侧 ----
A4 = """                _cjb_if_node = {
                    'type': 'If',
                    'test': _cjb_cond_expr,
                    'body': _cjb_then_stmts,
                    'orelse': _cjb_else_stmts if _cjb_else_stmts else None,
                }
                if _cjb_pre_stmts:
                    stmts.extend(_cjb_pre_stmts)
                stmts.append(_cjb_if_node)
"""

R4 = """                _cjb_if_node = {
                    'type': 'If',
                    'test': _cjb_cond_expr,
                    'body': _cjb_then_stmts,
                    'orelse': (_cjb_else_stmts
                               if (_cjb_else_stmts and not _cjb_else_is_join)
                               else None),
                }
                if _cjb_pre_stmts:
                    stmts.extend(_cjb_pre_stmts)
                stmts.append(_cjb_if_node)
                if _cjb_else_is_join and _cjb_else_stmts:
                    stmts.extend(_cjb_else_stmts)
"""

MARKER = '_cjb_target_is_arm_join'
ANCHORS = ((A1, R1), (A2, R2), (A3, R3), (A4, R4))


def main():
    only_check = '--check' in sys.argv
    raw = open(TARGET, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig' if has_bom else 'utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = text.replace('\r\n', '\n')

    if MARKER in norm:
        print('[fix167] already applied (marker present) — no change')
        return 0

    for a, _r in ANCHORS:
        n = norm.count(a)
        if n != 1:
            print('[fix167] FAILED: anchor count=%d (expected 1): %r' % (n, a.strip()[:60]))
            return 2

    new_norm = norm
    for a, r in ANCHORS:
        new_norm = new_norm.replace(a, r)
    if only_check:
        print('[fix167] check: patchable (all 4 anchors count=1), not applied')
        return 0

    out = new_norm.replace('\n', nl).encode('utf-8')
    expect = raw
    for a, r in ANCHORS:
        expect = expect.replace(a.replace('\n', nl).encode('utf-8'),
                                r.replace('\n', nl).encode('utf-8'))
    if out != expect:
        print('[fix167] FAILED: byte-level round-trip mismatch')
        return 3
    inserted = sum(r.count('\n') - a.count('\n') for a, r in ANCHORS)
    if out.count(nl.encode()) != raw.count(nl.encode()) + inserted:
        print('[fix167] FAILED: line-count accounting mismatch')
        return 4

    tmpdir = tempfile.mkdtemp(prefix='fix167_')
    tmp_py = os.path.join(tmpdir, 'patched.py')
    with open(tmp_py, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(tmp_py, cfile=tmp_py + 'c', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        print('[fix167] FAILED: patched source does not compile: %s' % exc)
        return 5

    with open(TARGET, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(TARGET, cfile=tmp_py + 'c2', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        with open(TARGET, 'wb') as f:
            f.write(raw)
        print('[fix167] ROLLED BACK: target does not compile: %s' % exc)
        return 6

    print('[fix167] applied: +%d lines, py_compile OK (%s%s)' % (
        inserted, TARGET, ', BOM preserved' if has_bom else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
