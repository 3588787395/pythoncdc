import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryRangeStep(ExhaustiveTestCase):
    """Bug R13 (new): range(0, 10, (a if c else b)) — range 三参数 ternary。

    原始:
        range(0, 10, (a if c else b))
    缺陷: ternary 作为 range 内置函数的第三个位置参数（step）。cond_block
         preload 含 PUSH_NULL + LOAD_GLOBAL range + LOAD_CONST 0 + LOAD_CONST
         10（前两个位置参数），ternary merge 块作为 range 调用第三个位置参数。
         验证 ternary 在多位置参数（3 个）场景下归约路径（R12 max_default 是
         1 positional + 1 kwarg 模式，R13 是 3 positional 模式）。
    """
    SOURCE_CODE = """range(0, 10, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
