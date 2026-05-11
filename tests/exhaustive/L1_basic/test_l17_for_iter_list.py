import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL17ForIterList(ExhaustiveTestCase):
    SOURCE_CODE = """for item in [1, 2, 3]:
    print(item)
"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
