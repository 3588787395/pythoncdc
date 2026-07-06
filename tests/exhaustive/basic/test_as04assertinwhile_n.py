import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs04AssertInWhile_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(lst):
    i = 0
    while i < len(lst):
        assert lst[i] is not None
        i += 1
"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
