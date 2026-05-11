import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE23TryFinallyAssign_a(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    a = 1
finally:
    a = 0"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
