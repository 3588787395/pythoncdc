import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryWithFstringFormatSpec(ExhaustiveTestCase):
    """Bug R2-42: ternary 在 f-string 中带 format spec — 字节码不一致。

    原始: x = f"{(a if cond else b):>5}"
    缺陷: ternary 在 f-string 中带 format spec 时，FORMAT_VALUE flags 含 has_format_spec
         位（flags & 4），且 format_spec 也是栈元素。反编译器可能丢失 format_spec。
    """
    SOURCE_CODE = '''x = f"{(a if cond else b):>5}"'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
