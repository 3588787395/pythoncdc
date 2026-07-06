import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL08WhileContinue(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    x -= 1
    if x % 2 == 0:
        continue
    print(x)
"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
