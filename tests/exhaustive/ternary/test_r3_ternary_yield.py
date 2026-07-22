import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryYieldInExpr(ExhaustiveTestCase):
    """Bug R3-14: ternary 在 yield 表达式（带算术）— 字节码不一致。

    原始:
        def g():
            yield (a if cond else 0) + 1
    缺陷: ternary 在 yield + 算术上下文中，YIELD_VALUE + BINARY_OP 在 merge_block
         中消费 ternary 结果。反编译器可能丢失 yield 或 +1 结构。
    """
    SOURCE_CODE = """def g():
    yield (a if cond else 0) + 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
