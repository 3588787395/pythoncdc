# -*- coding: utf-8 -*-
"""rr-v5r180 patch: cookiejar CJ5 DEEPRET (`_str2time`)。

用法：
    D:/Python/python.exe -I -X utf8 D:\\temp\\opencode\\cl_layout\\r180\\fix180.py [--revert]

唯一改动文件：core/cfg/region_ast_generator.py
判据：**v180-EXCRET**（handler 内显式 `return None` 不被 v116-FOLDRET 折叠守卫误杀）
约束：anchor count==1、UTF-8(无 BOM)、CRLF 保持、py_compile 通过、幂等（标记检测）。
"""
from __future__ import annotations

import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')
MARK = 'v180-EXCRET'

ANCHOR = (
    "                if (instr.opname == 'RETURN_VALUE'\r\n"
    "                        and len(stmt_instrs) == 1\r\n"
    "                        and stmt_instrs[0].opname == 'LOAD_CONST'\r\n"
    "                        and stmt_instrs[0].argval is None\r\n"
    "                        and getattr(stmt_instrs[0], 'starts_line', None) is None\r\n"
    "                        and not (getattr(getattr(self.cfg, 'code', None),\r\n"
    "                                         'co_flags', 0) & 0x20)):\r\n"
)

PATCH = (
    "                # [v180-EXCRET] handler 内显式 `return None` 的 POP_EXCEPT 形态\r\n"
    "                # （只增不破）：CPython 把 except 体内的显式 `return None` 编成\r\n"
    "                # POP_EXCEPT(#L<行号>) + LOAD_CONST None(starts_line=None) +\r\n"
    "                # RETURN_VALUE——行号落在 POP_EXCEPT 上、值装载对无行号，与\r\n"
    "                # v116-FOLDRET 的「编译器折叠隐式臂返回」签名逐位同形。v116\r\n"
    "                # 守卫据此把 handler 内的显式 `else: return None` 整条丢弃\r\n"
    "                # （cookiejar _str2time 实测少 JUMP_FORWARD/POP_EXCEPT/\r\n"
    "                # LOAD_CONST/RETURN_VALUE 4 条、异常表 target 130→122）。判据\r\n"
    "                # 只读本块自身指令的行号元数据（v116 守卫主判据用的同一字段）：\r\n"
    "                # 块内 POP_EXCEPT 带 starts_line ⇒ 该 RETURN 是源码显式\r\n"
    "                # return 语句（行号随 POP_EXCEPT 发射）；handler 自然收尾的\r\n"
    "                # 隐式返回其 POP_EXCEPT 无行号（tarfile makelink 实测）⇒ 仍\r\n"
    "                # 由 v116 折叠、产物逐字节不变（C3）。\r\n"
    "                if (instr.opname == 'RETURN_VALUE'\r\n"
    "                        and len(stmt_instrs) == 1\r\n"
    "                        and stmt_instrs[0].opname == 'LOAD_CONST'\r\n"
    "                        and stmt_instrs[0].argval is None\r\n"
    "                        and getattr(stmt_instrs[0], 'starts_line', None) is None\r\n"
    "                        and not any(_v180_i.opname == 'POP_EXCEPT'\r\n"
    "                                    and getattr(_v180_i, 'starts_line', None) is not None\r\n"
    "                                    for _v180_i in block.instructions)\r\n"
    "                        and not (getattr(getattr(self.cfg, 'code', None),\r\n"
    "                                         'co_flags', 0) & 0x20)):\r\n"
)


def main():
    revert = '--revert' in sys.argv
    src = io.open(TARGET, encoding='utf-8-sig', newline='').read()
    if revert:
        if MARK not in src:
            print('[fix180] already clean (no %s)' % MARK)
            return 0
        n = src.count(PATCH)
        if n != 1:
            print('[fix180] REVERT anchor count=%d (expected 1)' % n)
            return 2
        out = src.replace(PATCH, ANCHOR)
        io.open(TARGET, 'w', encoding='utf-8', newline='').write(out)
        py_compile.compile(TARGET, cfile=os.path.join(
            os.environ.get('TEMP', '.'), '_fix180_revert.pyc'), doraise=True)
        print('[fix180] reverted: %d -> %d chars' % (len(src), len(out)))
        return 0
    if MARK in src:
        print('[fix180] already patched (%s present)' % MARK)
        return 0
    n = src.count(ANCHOR)
    if n != 1:
        print('[fix180] ANCHOR count=%d (expected 1)' % n)
        return 2
    out = src.replace(ANCHOR, PATCH)
    io.open(TARGET, 'w', encoding='utf-8', newline='').write(out)
    py_compile.compile(TARGET, cfile=os.path.join(
        os.environ.get('TEMP', '.'), '_fix180_apply.pyc'), doraise=True)
    print('[fix180] patched: %d -> %d chars (%+d)' % (len(src), len(out), len(out) - len(src)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
