import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs03AssertInIf_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, flag):
    if flag:
        assert a != 0
    a = 0
"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
