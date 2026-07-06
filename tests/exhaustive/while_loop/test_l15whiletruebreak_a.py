import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL15WhileTrueBreak_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    a = 0
    while True:
        a += 1
        if a > 10:
            break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
