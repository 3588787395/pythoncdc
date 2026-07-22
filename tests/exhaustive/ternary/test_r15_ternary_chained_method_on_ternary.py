import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryChainedMethodOnTernary(ExhaustiveTestCase):
    """Bug R15 (new): (a if c else b).upper().lower() — chained method on ternary。

    原始:
        (a if c else b).upper().lower()
    缺陷: ternary 后接 chained method 调用 upper().lower()。ternary merge 块
         栈顶作为 LOAD_METHOD upper 的 receiver，CALL 0 后再 LOAD_METHOD lower +
         CALL 0。R13 method_chain_attr 已测 s.upper().split(ternary)（chain 含
         ternary 在末位），R15 测 chain 整体在 ternary 之后变体。
    """
    SOURCE_CODE = """(a if c else b).upper().lower()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
