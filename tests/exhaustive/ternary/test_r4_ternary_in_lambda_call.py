import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInLambdaCall(ExhaustiveTestCase):
    """Bug R4-12: ternary 在 lambda 体（带比较条件）— 字节码不一致。

    原始: f = lambda x: (a if x > 0 else b)
    缺陷: ternary 在 lambda 体中，且 ternary 条件是比较表达式时，
         嵌套 code object 内 COMPARE_OP + POP_JUMP_IF 构成 ternary 头，
         lambda body 的 RETURN_VALUE 是 implicit。
         反编译器可能丢失 lambda 或 ternary 结构。
    """
    SOURCE_CODE = """f = lambda x: (a if x > 0 else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
