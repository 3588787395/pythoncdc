import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN06While_For_Break_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data, target):
    i = 0
    while i < len(data):
        for item in data[i]:
            if item == target:
                break
        a = data[i]
        i += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
