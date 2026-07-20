import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryBodyIsBinop(ExhaustiveTestCase):
    """Bug R2-27: ternary body/orelse 是复合表达式 (a+1 if c else b*2) — 字节码不一致。

    原始: x = (a + 1) if cond else (b * 2)
    缺陷: ternary body 和 orelse 都含 BINARY_OP 时，true_value_block 和
         false_value_block 都不是单 LOAD 块。需 _is_single_expression_block
         接受 BINARY_OP 表达式块。
    """
    SOURCE_CODE = """x = (a + 1) if cond else (b * 2)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
