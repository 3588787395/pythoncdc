import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10FstringMethodCall(ExhaustiveTestCase):
    # if 体内 f-string 中包含方法调用
    SOURCE_CODE = """if c:
    x = f"{s.upper()}" """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
