# -*- coding: utf-8 -*-
"""rr-v5r181 patch: cookiejar CJ6 TRYELSE (`deepvalues`) —— else 臂自环协议块归属。

用法：
    D:/Python/python.exe -I -X utf8 D:\\temp\\opencode\\cl_layout\\r181\\fix181.py [--revert]

唯一改动文件：core/cfg/region_ast_generator.py
判据：**v181-TRYELSE-ARMSELF**（else 臂尾块的可达性判据对「自环前驱」豁免）
约束：anchor count==1、UTF-8(无 BOM)、CRLF 保持、py_compile 通过、幂等（标记检测）。
"""
from __future__ import annotations

import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')
MARK = 'v181-TRYELSE-ARMSELF'

ANCHOR = (
    "                            if all(id(_p) in _r27_arm for _p in _r27_ps):\r\n"
)

PATCH = (
    "                            # [v181-TRYELSE-ARMSELF] else 臂尾块可达性判据的\r\n"
    "                            # 自环前驱豁免（只增不破）。\r\n"
    "                            # 识别条件：R27-9 的 else 臂尾归属在\r\n"
    "                            # (max(else_blocks), min(handler_entry)) 区间上按「全部前驱\r\n"
    "                            # 已在臂内」做不动点扩展。CPython 3.11 把 try/except/else\r\n"
    "                            # 的 else 体内一条 `yield from X` 编成三段：setup 段\r\n"
    "                            # （…GET_YIELD_FROM_ITER; LOAD_CONST None）落在承接 else\r\n"
    "                            # 体的直落块尾部、SEND/YIELD_VALUE 自环块（轮询）、以及其\r\n"
    "                            # 后 POP_TOP 出口块。轮询块以自身为前驱（回边自指），于是\r\n"
    "                            # 「全部前驱在臂内」永不成立 ⇒ else 臂在轮询段之前的赋值处\r\n"
    "                            # 收尾，`yield from` 被宿主循环当 try 语句后的兄弟语句发射。\r\n"
    "                            # 重编译后 else 臂被截短：跳越 handler 的 JUMP_FORWARD 提前\r\n"
    "                            # 到 handler 之前、yield-from 整段 9 条指令搬到 handler 之后，\r\n"
    "                            # 异常表保护区间内容随之改变（cookiejar deepvalues 实测\r\n"
    "                            # 9 条指令搬位、异常表 (24,30,54) → (24,30,36)）。\r\n"
    "                            # 归约方式：候选块的**自前驱**（p is b，即块内回边自指）不算\r\n"
    "                            # 「臂外流入」——该边不引入任何臂外控制流，故不否决臂成员\r\n"
    "                            # 资格；非自前驱仍必须全部在臂内。判据只读 CFG 前驱身份与\r\n"
    "                            # 块偏移区间（I.4 白名单：无名字/无阈值/无异常表数值）。\r\n"
    "                            # 唯一归属：被认领的尾块仍走既有 else 臂发射循环，由\r\n"
    "                            # get_entry_region_for_block 派发其嵌套区域（is_yield_from_loop\r\n"
    "                            # 子 LoopRegion）整树重建 Expr(YieldFrom) → ast.Try.orelse；\r\n"
    "                            # try 体 / handler 入口 / finally / cleanup 块仍在 reserved 内\r\n"
    "                            # 不被认领。\r\n"
    "                            if all(id(_p) in _r27_arm or _p is _r27_b for _p in _r27_ps):\r\n"
)


def main():
    revert = '--revert' in sys.argv
    src = io.open(TARGET, encoding='utf-8-sig', newline='').read()
    if revert:
        if MARK not in src:
            print('[fix181] already clean (no %s)' % MARK)
            return 0
        n = src.count(PATCH)
        if n != 1:
            print('[fix181] REVERT anchor count=%d (expected 1)' % n)
            return 2
        out = src.replace(PATCH, ANCHOR)
        io.open(TARGET, 'w', encoding='utf-8', newline='').write(out)
        py_compile.compile(TARGET, cfile=os.path.join(
            os.environ.get('TEMP', '.'), '_fix181_revert.pyc'), doraise=True)
        print('[fix181] reverted: %d -> %d chars' % (len(src), len(out)))
        return 0
    if MARK in src:
        print('[fix181] already patched (%s present)' % MARK)
        return 0
    n = src.count(ANCHOR)
    if n != 1:
        print('[fix181] ANCHOR count=%d (expected 1)' % n)
        return 2
    out = src.replace(ANCHOR, PATCH)
    io.open(TARGET, 'w', encoding='utf-8', newline='').write(out)
    py_compile.compile(TARGET, cfile=os.path.join(
        os.environ.get('TEMP', '.'), '_fix181_apply.pyc'), doraise=True)
    print('[fix181] patched: %d -> %d chars (%+d)' % (len(src), len(out), len(out) - len(src)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
