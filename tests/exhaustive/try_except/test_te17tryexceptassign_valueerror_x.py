import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE17TryExceptAssign_ValueError_x(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    x = 1
except ValueError:
    x = 0"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
