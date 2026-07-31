import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6WhileTripleCmp(ExhaustiveTestCase):
    SOURCE_CODE = """a = 1
b = 2
c = 3
while a == b == c:
    a += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
