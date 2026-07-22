import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInCallStarred(ExhaustiveTestCase):
    """Bug R5-13: ternary 作为函数调用 starred 参数 — 字节码不一致。

    原始: f(*(a if c else b))
    缺陷: ternary 作为 *args 展开参数时，BUILD_LIST + LIST_EXTEND + LIST_TO_TUPLE
         在 merge_block 中消费 ternary 结果。R1 已通过简单 starred 场景
         （test_r1_ternary_in_starred）。R5 用唯一 *args 参数形式重测。
         期望：Call(func=f, args=[], starargs=IfExp) 正确归约。
    """
    SOURCE_CODE = """f(*(a if c else b))"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
