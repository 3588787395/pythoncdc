import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary11InIf(ExhaustiveTestCase):
    SOURCE_CODE = """if (a if c else b) > threshold:
    process()"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
