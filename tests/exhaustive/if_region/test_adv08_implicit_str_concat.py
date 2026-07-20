import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08ImplicitStrConcat(ExhaustiveTestCase):
    # if 体内隐式字符串连接 s = "a" "b" "c"
    SOURCE_CODE = '''if c:
    s = "a" "b" "c"'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
