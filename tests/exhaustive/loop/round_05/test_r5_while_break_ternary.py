import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5WhileBreakTernary(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    while a:
        if (x if cond else y):
            break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
