import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestE02MultiExcept_ValueError_AttributeError_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    try:
        int(n)
    except (ValueError, AttributeError):
        n = 0"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
