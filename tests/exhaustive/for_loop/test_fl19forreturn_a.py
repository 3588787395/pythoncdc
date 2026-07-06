import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL19ForReturn_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for a in range(10):
        if a == 5:
            return a"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
