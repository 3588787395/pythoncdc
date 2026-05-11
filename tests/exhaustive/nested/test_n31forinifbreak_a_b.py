import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN31ForInIfBreak_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    for b in range(10):
        if b > 5:
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
