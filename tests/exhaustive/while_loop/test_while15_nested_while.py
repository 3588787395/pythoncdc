import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile15NestedWhile(ExhaustiveTestCase):
    SOURCE_CODE = """while rows:
    row = rows.pop(0)
    cols = list(row)
    while cols:
        val = cols.pop(0)
        process(val)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
