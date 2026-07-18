import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05FstringFormatSpec(ExhaustiveTestCase):
    # if 体内 f-string 嵌套格式说明符
    SOURCE_CODE = """if c:
    s = f'{x:{width}.2f}'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
