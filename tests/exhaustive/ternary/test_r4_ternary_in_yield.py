import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInYield(ExhaustiveTestCase):
    """Bug R4-17: ternary 在 yield 表达式（带显式括号）— 字节码不一致。

    原始:
        def g():
            yield (a if cond else b)
    缺陷: ternary 在 yield 表达式中时，YIELD_VALUE 在 merge_block 中消费
         ternary 结果。R2 已测无括号版本，R4 增加显式括号以分离括号语义影响。
         反编译器可能丢失 yield 结构。
    """
    SOURCE_CODE = """def g():
    yield (a if cond else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
