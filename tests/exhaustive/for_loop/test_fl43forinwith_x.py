import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL43ForInWith_x(ExhaustiveTestCase):
    SOURCE_CODE = """with open("data.txt") as fh:
    for x in range(5):
        y = x + 1"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
