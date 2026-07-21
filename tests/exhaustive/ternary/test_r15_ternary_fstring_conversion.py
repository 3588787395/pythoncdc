import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryFstringConversion(ExhaustiveTestCase):
    """Bug R15 (new): f"{(a if c else b)!r}" — fstring with conversion。

    原始:
        f"{(a if c else b)!r}"
    缺陷: ternary 作为 f-string 表达式部分，带 !r 转换。R2/R4/R8 已测 fstring
         + ternary，R15 测带 !r 转换的变体。FORMAT_VALUE 指令 arg 含 conversion
         flag，可能引发 conversion flag 丢失。
    """
    SOURCE_CODE = '''f"{(a if c else b)!r}"
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
