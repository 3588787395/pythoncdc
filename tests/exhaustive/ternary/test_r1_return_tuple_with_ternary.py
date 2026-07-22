import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1ReturnTupleWithTernary(ExhaustiveTestCase):
    """Bug 10: return (ternary, other) — 嵌套 code object 字节码不一致。

    原始:
        def f():
            return (a if cond else b), c
    错误反编译:
        def f():
            (a if cond else b,)
    缺陷: 原始是 BUILD_TUPLE 2 (含 ternary + c) 后 RETURN_VALUE。
         反编译器在嵌套函数 code object 中丢失了 c 元素，
         BUILD_TUPLE 2 退化为 BUILD_TUPLE 1，且增加 POP_TOP/LOAD_CONST None。
         IfExp 在 AST 中存在，但函数字节码指令序列不一致。
    """
    SOURCE_CODE = """def f():
    return (a if cond else b), c"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
