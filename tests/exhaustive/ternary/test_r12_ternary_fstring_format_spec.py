import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryFstringFormatSpec(ExhaustiveTestCase):
    """Bug R12 (new): f"{x:{(a if c else b)}}" — ternary 在 format spec。

    原始:
        r = f"{x:{(a if c else b)}}"
    缺陷: ternary 在 f-string 的 format spec 内。FORMAT_VALUE + BUILD_STRING
         序列中，format spec 部分是独立的 LOAD + FORMAT_VALUE 0x03（带 spec）。
         ternary merge 块的栈输出作为 FORMAT_VALUE 的 spec 参数。R8 已测过
         f-string nested format spec (test_r8_ternary_in_fstring_format_spec)，
         R12 测更直接的 spec=ternary 形式（变量 x 的 format spec 是 ternary）。
    """
    SOURCE_CODE = '''r = f"{x:{(a if c else b)}}"
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
