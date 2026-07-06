import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN13Try_For_If_Break_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    try:
        for item in items:
            if item is not None and item < 0:
                break
            a = item
    except IndexError:
        a = None"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
