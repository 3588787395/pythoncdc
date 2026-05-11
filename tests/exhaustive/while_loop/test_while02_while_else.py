import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile02WhileElse(ExhaustiveTestCase):
    SOURCE_CODE = """while items:
    item = items.pop()
    process(item)
else:
    print("empty")"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
