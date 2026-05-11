import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_For_If_While_v1(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    if y > 0:
        while z > 0:
            z -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
