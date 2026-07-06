import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestE02MultiExcept_TypeError_KeyError_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(d, key):
    try:
        d[key]
    except (TypeError, KeyError):
        d = {}"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
