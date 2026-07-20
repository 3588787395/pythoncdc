import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11WalrusTernaryIfCond(ExhaustiveTestCase):
    # if 条件中海象赋值的三元表达式值 if (n := a if b else c):
    SOURCE_CODE = """if (n := a if b else c):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
