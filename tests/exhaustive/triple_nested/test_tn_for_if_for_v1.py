import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN_For_If_For_v1(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    if y > 0:
        for z in range(3):
            pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
