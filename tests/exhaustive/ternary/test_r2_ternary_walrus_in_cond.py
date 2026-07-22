import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryWalrusInCond(ExhaustiveTestCase):
    """Bug R2-38: ternary 条件中含 walrus 表达式 — 字节码不一致。

    原始: x = a if (y := cond) else b
    缺陷: walrus 在 ternary 条件中时，condition_block 含 COPY 1 + STORE_* 序列。
         _is_single_expression_block 应允许此模式，但 condition_block 通常
         不被 _is_single_expression_block 校验，需检查 _build_ternary_value_expr。
    """
    SOURCE_CODE = """x = a if (y := cond) else b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
