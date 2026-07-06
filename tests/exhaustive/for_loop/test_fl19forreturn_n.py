import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL19ForReturn_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for n in range(10):
        if n == 5:
            return n"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
