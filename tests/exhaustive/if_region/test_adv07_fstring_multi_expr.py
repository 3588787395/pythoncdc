import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07FstringMultiExpr(ExhaustiveTestCase):
    # if 体内 f-string 多表达式: f"{a + b}{c * d}{e}"
    SOURCE_CODE = '''if c:
    s = f"{a + b}{c * d}{e}"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
