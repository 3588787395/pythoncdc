import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryYieldInBinopChain(ExhaustiveTestCase):
    """Bug R14 (new): yield (a if c else b) * 2 + 1 — yield 表达式含 chained binop。

    原始:
        def gen():
            yield (a if c else b) * 2 + 1
    缺陷: ternary 作为 yield 表达式，且 ternary 后续有两个 BINARY_OP（先 *2 再 +1）。
         R14 yield_with_binop 测一个 binop。R14 chain 变体测两个 binop 链：
         ternary merge 之后 BINARY_OP * 2 + BINARY_OP + 1 + YIELD_VALUE，验证
         多个 BINARY_OP 消费链能否完整保留。
    """
    SOURCE_CODE = """def gen():
    yield (a if c else b) * 2 + 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
