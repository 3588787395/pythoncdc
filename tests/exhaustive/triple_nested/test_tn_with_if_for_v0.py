import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_With_If_For_v0(ExhaustiveTestCase):
    SOURCE_CODE = """with open('f') as f:
    if m > 0:
        for k in range(3):
            pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
