import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL29WhileElseMulti_x(ExhaustiveTestCase):
    SOURCE_CODE = """x = 5
while x > 0:
    x = x - 1
else:
    a = 1
    b = 2
    c = a + b"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
