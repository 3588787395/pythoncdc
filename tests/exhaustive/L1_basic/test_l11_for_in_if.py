import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL11ForInIf(ExhaustiveTestCase):
    SOURCE_CODE = """if condition:
    for i in range(10):
        print(i)
"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
