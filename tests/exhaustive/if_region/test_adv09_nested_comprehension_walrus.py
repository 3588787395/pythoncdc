import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09NestedComprehensionWalrus(ExhaustiveTestCase):
    # if 体内嵌套推导式带 walrus r = [[y := x for x in a] for a in b]
    SOURCE_CODE = """if c:
    r = [[y := x for x in a] for a in b]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
