import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6WhileCompoundAndOr(ExhaustiveTestCase):
    SOURCE_CODE = """a = 1
b = 2
while a < 5 and b < 5 or a == 1:
    a += 1
    b += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
