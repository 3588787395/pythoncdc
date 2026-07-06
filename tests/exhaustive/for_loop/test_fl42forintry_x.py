import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL42ForInTry_x(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    for x in range(5):
        y = 10 // x
except ZeroDivisionError:
    y = 0"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
