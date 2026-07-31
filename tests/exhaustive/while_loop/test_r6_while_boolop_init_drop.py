import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6WhileBoolopInitDrop(ExhaustiveTestCase):
    SOURCE_CODE = """a = 0
while a < 3 or a < 6:
    a += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
