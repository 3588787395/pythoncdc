import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL41ForInWhile_x(ExhaustiveTestCase):
    SOURCE_CODE = """x = 10
while x > 0:
    for j in range(2):
        x = x - 1
    x = x - 2"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
