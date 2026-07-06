import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIf14ElifWithNested(ExhaustiveTestCase):
    SOURCE_CODE = """if x:
    y = 1
elif z:
    if w:
        v = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
