import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN35DeepNested_a_b_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    for b in range(3):
        try:
            if b == 1:
                pass
        except IndexError:
            pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
