import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL32ForElseMulti_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(5):
    x = x * 2
else:
    a = 1
    b = 2
    c = a + b"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
