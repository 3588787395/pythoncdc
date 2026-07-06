import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL13ForWithReturn(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(10):
    if i == 5:
        return i
    print(i)
"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
