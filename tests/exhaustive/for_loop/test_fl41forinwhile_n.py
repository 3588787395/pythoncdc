import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL41ForInWhile_n(ExhaustiveTestCase):
    SOURCE_CODE = """n = 0
while n < 5:
    for i in range(3):
        n = n + i
    n = n + 1"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
