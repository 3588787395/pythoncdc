import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF32NestedIfElse_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    if b > 0:
        a = 1
    else:
        a = 2
else:
    a = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
