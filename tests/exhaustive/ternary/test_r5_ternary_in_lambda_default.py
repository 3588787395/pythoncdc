import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInLambdaDefault(ExhaustiveTestCase):
    """Bug R5-12: ternary 作为 lambda 默认参数 — 字节码不一致。

    原始: f = lambda x=(a if c else b): x
    缺陷: ternary 作为 lambda 默认参数时，MAKE_FUNCTION 在 merge_block 中
         消费 ternary 结果作为 default tuple 元素。R2 已通过简单默认参数场景
         （test_r2_ternary_in_default_arg）。R5 用 lambda（非 def）+ 默认参数
         形式加重复杂度。期望：lambda defaults 正确归约含 IfExp。
    """
    SOURCE_CODE = """f = lambda x=(a if c else b): x"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
