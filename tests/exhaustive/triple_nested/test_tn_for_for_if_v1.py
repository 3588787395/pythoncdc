import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_For_For_If_v1(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    for y in range(5):
        if z > 0:
            z -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
