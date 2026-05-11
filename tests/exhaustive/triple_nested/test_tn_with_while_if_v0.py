import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_With_While_If_v0(ExhaustiveTestCase):
    SOURCE_CODE = """with open('f') as f:
    while m > 0:
        if k > 0:
            k -= 1
        m -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
