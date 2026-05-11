import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_While_For_While_v0(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    for m in range(5):
        while k > 0:
            k -= 1
    n -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
