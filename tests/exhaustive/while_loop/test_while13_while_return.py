import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile13WhileReturn(ExhaustiveTestCase):
    SOURCE_CODE = """def find_match(items):
    while items:
        item = items.pop()
        if matches(item):
            return item
    return None"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
