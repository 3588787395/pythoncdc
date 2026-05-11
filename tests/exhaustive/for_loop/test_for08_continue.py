import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor08Continue(ExhaustiveTestCase):
    SOURCE_CODE = """result = []
for i in range(10):
    if i % 2 == 0:
        continue
    result.append(i)"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
