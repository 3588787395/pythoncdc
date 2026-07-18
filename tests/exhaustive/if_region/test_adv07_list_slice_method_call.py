import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07ListSliceMethodCall(ExhaustiveTestCase):
    # if 体内 list 切片 + 方法调用: a[1:2].count(x)
    SOURCE_CODE = """if c:
    r = a[1:2].count(x)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
