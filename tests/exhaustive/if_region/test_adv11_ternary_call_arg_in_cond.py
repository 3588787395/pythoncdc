import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TernaryCallArgInCond(ExhaustiveTestCase):
    # if 条件中函数调用参数为三元 if f(a if b else c):
    SOURCE_CODE = """if f(a if b else c):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
