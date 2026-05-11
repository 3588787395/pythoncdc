import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs01AssertBasic_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    assert n != ""
"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
