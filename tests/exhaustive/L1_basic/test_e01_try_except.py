import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestE01TryExcept(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    x = 1 / 0
except ZeroDivisionError:
    print("division by zero")
"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
