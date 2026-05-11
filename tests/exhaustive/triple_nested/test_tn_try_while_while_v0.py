import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_Try_While_While_v0(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    while m > 0:
        while k > 0:
            k -= 1
        m -= 1
except Exception:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
