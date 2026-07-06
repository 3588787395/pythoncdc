import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC05Nested_If_In_If_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n, m):
    if n > 10:
        if m > 10:
            n = m"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
