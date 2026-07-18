import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07StarredTupleValue(ExhaustiveTestCase):
    # if 体内星号表达式作 tuple 字面量元素 (value 位置): r = (a, *b, c)
    SOURCE_CODE = """if c:
    r = (a, *b, cc)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
