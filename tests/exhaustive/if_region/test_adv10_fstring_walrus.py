import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10FstringWalrus(ExhaustiveTestCase):
    # if 体内 f-string 中包含 walrus 表达式
    SOURCE_CODE = """if c:
    x = f"{(y := f())}" """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
