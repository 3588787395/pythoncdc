import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN05While_If_Continue_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, limit):
    while x < limit:
        if x < 0:
            continue
        a = x * 2
        x += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
