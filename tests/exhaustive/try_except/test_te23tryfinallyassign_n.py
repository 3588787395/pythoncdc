import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE23TryFinallyAssign_n(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    n = 1
finally:
    n = 0"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
