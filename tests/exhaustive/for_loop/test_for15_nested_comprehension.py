import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor15NestedComprehension(ExhaustiveTestCase):
    SOURCE_CODE = """result = []
for row in matrix:
    for val in row:
        result.append(val)"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
