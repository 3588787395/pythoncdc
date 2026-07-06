import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE24TryExceptFinallyAssign_IndexError_a(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    a = 1
except IndexError:
    a = 0
finally:
    a = -1"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
