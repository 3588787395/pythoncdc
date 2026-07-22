import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryReturnTuple(ExhaustiveTestCase):
    """Bug R3-18: 多个 ternary 在 return tuple 中 — 字节码不一致。

    原始:
        def f():
            return (a if cond else b), (c if cond else d)
    缺陷: 多个 ternary 作为 return tuple 元素时，BUILD_TUPLE 在 merge_block 中
         消费两个 ternary 结果。反编译器可能丢失 tuple 结构或第二个 ternary。
    """
    SOURCE_CODE = """def f():
    return (a if cond else b), (c if cond else d)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
