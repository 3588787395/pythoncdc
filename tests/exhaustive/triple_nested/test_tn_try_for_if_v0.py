import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_Try_For_If_v0(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    for m in range(5):
        if k > 0:
            k -= 1
except Exception:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
