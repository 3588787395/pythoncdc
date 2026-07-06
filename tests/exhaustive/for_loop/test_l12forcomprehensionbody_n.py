import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL12ForComprehensionBody_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    result = []
    for item in items:
        if item > 0:
            n = item * 2
            result.append(n)"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
