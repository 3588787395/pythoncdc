import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor18ForReturn(ExhaustiveTestCase):
    SOURCE_CODE = """def find_first(items):
    for item in items:
        if condition(item):
            return item
    return None"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
