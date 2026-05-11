import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIf12NestedIfElse(ExhaustiveTestCase):
    SOURCE_CODE = """if x:
    if y:
        a = 1
    else:
        b = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
