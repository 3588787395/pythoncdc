import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN04While_If_Break_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, limit):
    while x < limit:
        if x > 100:
            break
        x += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
