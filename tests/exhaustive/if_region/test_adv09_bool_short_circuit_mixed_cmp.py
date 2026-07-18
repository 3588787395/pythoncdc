import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09BoolShortCircuitMixedCmp(ExhaustiveTestCase):
    # if 条件混合比较和调用 f() and g() > 0 or h() == 1
    SOURCE_CODE = """if f() and g() > 0 or h() == 1:
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
