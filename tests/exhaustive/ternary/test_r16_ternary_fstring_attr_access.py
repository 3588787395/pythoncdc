import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryFstringAttrAccess(ExhaustiveTestCase):
    """Bug R16 (new): f"{(a if c else b).x}" — fstring FormattedValue attr。

    原始:
        f"{(a if c else b).x}"
    缺陷: ternary 作为 f-string FormattedValue 的值 + .x attribute access。
         ternary merge 块栈顶经 LOAD_ATTR x + FORMAT_VALUE 1 (attr) +
         BUILD_STRING 1 消费链。R8 fstring_nested 已测过嵌套 ternary in
         f-string，R16 测 ternary.attr 模式。
    """
    SOURCE_CODE = '''f"{(a if c else b).x}"
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
