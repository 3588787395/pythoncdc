import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry01Basic(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    x = 1 / 0
except ZeroDivisionError:
    x = 0"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
