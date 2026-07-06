import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile11WhileIf(ExhaustiveTestCase):
    SOURCE_CODE = """while data:
    item = data.pop(0)
    if valid(item):
        results.append(item)"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
