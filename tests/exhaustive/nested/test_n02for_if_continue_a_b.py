import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN02For_If_Continue_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items, threshold):
    for item in items:
        if item <= threshold:
            continue
        a = item"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
