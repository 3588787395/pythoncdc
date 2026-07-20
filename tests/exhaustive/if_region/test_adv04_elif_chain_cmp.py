import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04ElifChainCmp(ExhaustiveTestCase):
    # elif 链中链式比较归约
    SOURCE_CODE = """if a:
    pass
elif 0 < b < 10:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
