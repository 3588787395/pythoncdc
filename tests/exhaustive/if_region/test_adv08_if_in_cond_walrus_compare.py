import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08IfInCondWalrusCompare(ExhaustiveTestCase):
    # if 条件含 walrus + 复杂比较组合 if (n := f()) > 0 and (n := g()) < 10:
    SOURCE_CODE = """if (n := f()) > 0 and (n := g()) < 10:
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
