import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernarySliceStep(ExhaustiveTestCase):
    """Bug R13 (new): x[a:b:c if d else e] — slice with ternary step。

    原始:
        x[a:b:c if d else e]
    缺陷: ternary 作为 slice 的第三个维度（step）。BUILD_SLICE 3 指令
         消费 3 个栈项（lower, upper, step）。ternary merge 块栈输出作为
         step 维度。R2 已测 ternary_in_slice (单维 a:ternary)，R2 已测
         ternary_in_slice_step (step=ternary 单维)。R13 测完整 a:b:ternary
         三参数 slice 变体。
    """
    SOURCE_CODE = """x[a:b:c if d else e]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
