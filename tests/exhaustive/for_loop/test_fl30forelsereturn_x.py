import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL30ForElseReturn_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    for x in range(5):
        x = x + 1
    else:
        return x"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
