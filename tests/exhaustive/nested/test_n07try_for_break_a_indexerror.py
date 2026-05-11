import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN07Try_For_Break_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    try:
        for item in items:
            if item < 0:
                break
            a = item
    except IndexError:
        items = []"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
