import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryClassAttr(ExhaustiveTestCase):
    """Bug R3-12: ternary 作为类属性 — 字节码不一致。

    原始:
        class A:
            x = a if cond else b
    缺陷: ternary 作为类属性时，LOAD_NAME + STORE_NAME 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失 ternary 结构。
    """
    SOURCE_CODE = """class A:
    x = a if cond else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
