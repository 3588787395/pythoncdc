import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09CompareChainTernaryOperand(ExhaustiveTestCase):
    # if 条件含链式比较中段为三元 0 < (a if c else b) < 10
    SOURCE_CODE = """if 0 < (a if c else b) < 10:
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
