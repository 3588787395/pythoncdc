import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIf15ElseWithNested(ExhaustiveTestCase):
    SOURCE_CODE = """if x:
    y = 1
else:
    if z:
        w = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
