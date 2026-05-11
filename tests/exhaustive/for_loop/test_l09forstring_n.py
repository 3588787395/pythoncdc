import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL09ForString_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(s):
    for ch in s:
        n = ch.upper()"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
