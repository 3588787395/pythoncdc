import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6WhileAndThree(ExhaustiveTestCase):
    SOURCE_CODE = """a = 0
b = 0
c = 0
while a < 1 and b < 1 and c < 1:
    a += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
