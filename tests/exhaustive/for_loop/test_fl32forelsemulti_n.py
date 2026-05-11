import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL32ForElseMulti_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    x = n
else:
    y = -1
    z = 0
    w = y + z"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
