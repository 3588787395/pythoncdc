import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL28WhileElsePrint_n(ExhaustiveTestCase):
    SOURCE_CODE = """n = 10
while n > 0:
    n -= 1
else:
    print(n)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
