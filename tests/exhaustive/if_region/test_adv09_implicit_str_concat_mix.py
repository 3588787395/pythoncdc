import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09ImplicitStrConcatMix(ExhaustiveTestCase):
    # if 体内隐式字符串连接混合 f-string 和字节串
    SOURCE_CODE = """if c:
    s = "a" 'b' "c" 'd'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
