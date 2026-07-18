import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08TupleCompareCond(ExhaustiveTestCase):
    # if 条件含元组比较 if (a, b) == (c, d):
    SOURCE_CODE = """if (a, b) == (c, d):
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
