import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL18NestedFor_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(rows):
    for row in rows:
        for item in row:
            x = item"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
