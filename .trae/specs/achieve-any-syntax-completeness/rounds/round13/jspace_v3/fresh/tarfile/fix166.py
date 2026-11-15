#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r166 单单元修复：TarFile._check —— elif 臂尾的隐式汇流 sink 不得作为语句发射。

缺陷（实证：rise r166/diff_check.txt）
------------------------------------
原始 pyc 32 指令与产物 32 指令逐条相同，只有两条条件跳转的目标块互换：
    74 POP_JUMP_FORWARD_IF_NONE  orig->140 / prod->144
    92 POP_JUMP_FORWARD_IF_FALSE orig->144 / prod->140
两目标块都是 `LOAD_CONST None; RETURN_VALUE`。产物在 elif 臂尾多发射了一条
`return None`（臂体 = [If, Return]），重编译后 CPython 把这两条跳转的目标
分配成相反的顺序。

判据（本补丁只加这一处）
------------------------
解析端把函数尾两个 trivial 返回块之一归进了 elif 臂体（region.elif_bodies[0]
末块），生成端 `_if_generate_elif_chain` 原有的「臂尾隐式 return None 弹出」
闸门只认 `_r23n16_blocks_have_explicit_return`（末块以 RETURN_VALUE 结尾即视为
显式），于是这块 sink 被当语句发射。新增闸门（C3：不命中逐字节回退）：

  臂末块无后继 + `_check_block_has_trailing_return_none`（裸 LOAD_CONST None;
  RETURN_VALUE）+ `_block_has_fallthrough_predecessor` 为假（W14-B：仅跳转边
  可达的函数尾 trivial 块）+ 末语句无 `_explicit_return` 指令背书
  → 该 Return None 是编译器产物，弹出。

反例保护：源码显式 `return None`（有 fallthrough 前驱，_w14_explicit_return_flag
或本判据）、except handler 内 return（POP_EXCEPT 块，非裸 sink）、多条件边汇合
return（_w14_join_bare_return_none）都不命中，输出不变。

用法
----
  python -I -X utf8 fix166.py          # 打补丁（幂等）
  python -I -X utf8 fix166.py --check  # 只检查当前状态
"""
import os
import py_compile
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')

ANCHOR = """            _elif_body_has_explicit_return = self._r23n16_blocks_have_explicit_return(region.elif_bodies[0])
            if not _elif_body_has_explicit_return:
                while (elif_body_stmts and
                       isinstance(elif_body_stmts[-1], dict) and
                       elif_body_stmts[-1].get('type') == 'Return' and
                       isinstance(elif_body_stmts[-1].get('value'), dict) and
                       elif_body_stmts[-1]['value'].get('type') == 'Constant' and
                       elif_body_stmts[-1]['value'].get('value') is None):
                    elif_body_stmts.pop()
"""

REPLACEMENT = """            _elif_body_has_explicit_return = self._r23n16_blocks_have_explicit_return(region.elif_bodies[0])
            # [r166-CHECKARM] 区域归约算法原则 1（块 = 前导语句 + 尾跳转）＋
            # 原则 2（每块唯一归属）：CPython 3.11 对 `if A and B: <体>` 的 and 链
            # 有两条假出口，各自落进一个 trivial 返回块（本形为 140 与 144，都是
            # `LOAD_CONST None; RETURN_VALUE`）。解析端把其中一块归进 elif 臂体时，
            # 它只是函数尾隐式返回的编译器产物，不是源码语句——发射它会让重编译
            # 多出 LOAD_CONST/RETURN_VALUE，并把两条条件跳转的目标块互换
            # （TarFile._check：74 IF_NONE 140↔144、92 IF_FALSE 144↔140）。
            # 判据只读臂末块后继集 + 末指令形态（_check_block_has_trailing_return_none）
            # + W14-B 的 fallthrough 前驱否证 + 语句的 _explicit_return 指令背书：
            # 源码显式 return None（有 fallthrough 前驱）、except handler 内 return、
            # 多条件边汇合的 return（W14-B 三判据）都带背书，本闸门不命中，行为不变。
            _elif_tail_implicit_sink = False
            if region.elif_bodies and region.elif_bodies[0]:
                _etb_sink = region.elif_bodies[0][-1]
                if (not list(getattr(_etb_sink, 'successors', ()) or ())
                        and self.region_analyzer._check_block_has_trailing_return_none(_etb_sink)
                        and not self._block_has_fallthrough_predecessor(_etb_sink)):
                    _elif_tail_implicit_sink = True
            if (not _elif_body_has_explicit_return
                    or (_elif_tail_implicit_sink
                        and elif_body_stmts
                        and isinstance(elif_body_stmts[-1], dict)
                        and not elif_body_stmts[-1].get('_explicit_return'))):
                while (elif_body_stmts and
                       isinstance(elif_body_stmts[-1], dict) and
                       elif_body_stmts[-1].get('type') == 'Return' and
                       isinstance(elif_body_stmts[-1].get('value'), dict) and
                       elif_body_stmts[-1]['value'].get('type') == 'Constant' and
                       elif_body_stmts[-1]['value'].get('value') is None):
                    elif_body_stmts.pop()
"""

MARKER = '_elif_tail_implicit_sink'
INSERTED_LINES = REPLACEMENT.count('\n') - ANCHOR.count('\n')


def main():
    only_check = '--check' in sys.argv
    raw = open(TARGET, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    codec = 'utf-8-sig' if has_bom else 'utf-8'
    text = raw.decode(codec)
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = text.replace('\r\n', '\n')

    if MARKER in norm:
        print('[fix166] already applied (marker present) — no change')
        return 0

    n = norm.count(ANCHOR)
    if n != 1:
        print('[fix166] FAILED: anchor count=%d (expected 1)' % n)
        return 2

    new_norm = norm.replace(ANCHOR, REPLACEMENT)
    if only_check:
        print('[fix166] check: patchable (anchor count=1), not applied')
        return 0

    out = new_norm.replace('\n', nl).encode('utf-8')
    expect = raw.replace(ANCHOR.replace('\n', nl).encode('utf-8'),
                         REPLACEMENT.replace('\n', nl).encode('utf-8'))
    if out != expect:
        print('[fix166] FAILED: byte-level round-trip mismatch')
        return 3
    if out.count(nl.encode()) != raw.count(nl.encode()) + INSERTED_LINES:
        print('[fix166] FAILED: line-count accounting mismatch')
        return 4

    tmpdir = tempfile.mkdtemp(prefix='fix166_')
    tmp_py = os.path.join(tmpdir, 'patched.py')
    with open(tmp_py, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(tmp_py, cfile=tmp_py + 'c', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        print('[fix166] FAILED: patched source does not compile: %s' % exc)
        return 5

    with open(TARGET, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(TARGET, cfile=tmp_py + 'c2', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        with open(TARGET, 'wb') as f:
            f.write(raw)
        print('[fix166] ROLLED BACK: target does not compile: %s' % exc)
        return 6

    print('[fix166] applied: +%d lines, py_compile OK (%s%s)' % (
        INSERTED_LINES, TARGET, ', BOM preserved' if has_bom else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
