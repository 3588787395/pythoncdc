import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInLambdaCall(ExhaustiveTestCase):
    """Bug R2-29: ternary 作为 lambda 调用参数 — 字节码不一致。

    原始: (lambda x: x * 2)(a if cond else 0)
    缺陷: lambda 调用 ternary 时，MAKE_FUNCTION + PRECALL + CALL 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失 lambda 调用结构。
    """
    SOURCE_CODE = """(lambda x: x * 2)(a if cond else 0)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
