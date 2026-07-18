import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10FstringFormatSpecExpr(ExhaustiveTestCase):
    # if 体内 f-string 中 format spec 包含表达式 f"{x:{width}}"
    SOURCE_CODE = """if c:
    x = f"{y:{width}}" """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
