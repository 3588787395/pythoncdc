import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInMultiTargetAssign(ExhaustiveTestCase):
    """Bug R2-41: ternary 作为多目标赋值的 RHS — 字节码不一致。

    原始: x = y = a if cond else b
    缺陷: ternary 作为多目标赋值的 RHS 时，STORE_NAME x + STORE_NAME y 在 merge_block
         中先后消费 ternary 结果。反编译器可能丢失 y = 赋值。
    """
    SOURCE_CODE = """x = y = a if cond else b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
