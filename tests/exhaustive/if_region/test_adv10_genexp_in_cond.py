import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10GenexpInCond(ExhaustiveTestCase):
    # if 条件中包含生成器表达式 any(x > 0 for x in lst)
    SOURCE_CODE = """if any(x > 0 for x in lst):
    y = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
