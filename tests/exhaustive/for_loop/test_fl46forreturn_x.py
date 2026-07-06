import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL46ForReturn_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for x in range(5):
        if x == 3:
            return x
    return -1"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
