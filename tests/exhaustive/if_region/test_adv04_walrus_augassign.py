import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04WalrusAugassign(ExhaustiveTestCase):
    # walrus + AugAssign（y += (n := f())）
    SOURCE_CODE = """if c:
    y += (n := f())"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
