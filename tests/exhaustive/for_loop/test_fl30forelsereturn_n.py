import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL30ForElseReturn_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for n in range(10):
        x = n
    else:
        return -1"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
