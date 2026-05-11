import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestE02MultiExcept_IndexError_ZeroDivisionError_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    try:
        x[0] / 0
    except (IndexError, ZeroDivisionError):
        x = []"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
