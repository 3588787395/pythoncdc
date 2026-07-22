import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryFstringFormatSpec(ExhaustiveTestCase):
    """Bug R15 (new): f"{x:{(a if c else b)}}" — fstring format spec ternary。

    原始:
        f"{x:{(a if c else b)}}"
    缺陷: ternary 作为 f-string format_spec 表达式（嵌套 {}）。R8/R12 已测
         fstring format spec，R15 测嵌套 ternary 在 format_spec 中的变体。
         FORMAT_VALUE + BUILD_STRING 链路消费 ternary 输出。
    """
    SOURCE_CODE = '''f"{x:{(a if c else b)}}"
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
