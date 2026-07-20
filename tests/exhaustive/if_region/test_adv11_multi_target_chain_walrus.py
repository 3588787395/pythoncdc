import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11MultiTargetChainWalrus(ExhaustiveTestCase):
    # if 体内多重赋值链 + walrus x = y = (z := f())
    SOURCE_CODE = """if c:
    x = y = (z := f())"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
