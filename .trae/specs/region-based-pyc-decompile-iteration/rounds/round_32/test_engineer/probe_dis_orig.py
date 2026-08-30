# -*- coding: utf-8 -*-
"""dis 原始 pyc 中两个不匹配函数的字节码，并输出反编译产物对应函数源码片段。"""
import dis
import marshal
import importlib.util
import sys

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
TARGETS = {"order_response_order_update", "trade_response_order_update"}


def load_code(pyc):
    with open(pyc, "rb") as f:
        f.read(16)
        return marshal.load(f)


def find_funcs(code, out):
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            if const.co_name in TARGETS:
                out.append(const)
            find_funcs(const, out)


def find_method_in_class(code, out):
    # 搜索类内方法（co_name 可能重复，找类限定名）
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            if const.co_name in TARGETS:
                out.append(const)
            find_method_in_class(const, out)


root = load_code(PYC)
found = []
find_method_in_class(root, found)
for fn in found:
    print("=" * 70)
    print("FUNC:", fn.co_name, "qual:", fn.co_qualname, "n_ins:", len(list(dis.get_instructions(fn))))
    dis.dis(fn)
    print()
