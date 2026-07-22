import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryKwonlyDefault(ExhaustiveTestCase):
    """Bug R10-15 (re-verify in R11): ternary in default of kwonly arg.

    原始:
        def f(*args, x=(a if c else b)):
            pass
    缺陷: ternary 作为 kwonly 参数 x 的默认值。kwonly 默认值通过
         BUILD_CONST_KEY_MAP 而非 BUILD_TUPLE 构建。ternary merge 块的栈输出
         作为 BUILD_CONST_KEY_MAP 的 value，KW_NAMES + LOAD_CONST ('x',) +
         ternary merge + BUILD_CONST_KEY_MAP + MAKE_FUNCTION。
    """
    SOURCE_CODE = """def f(*args, x=(a if c else b)):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
