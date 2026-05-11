import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs04AssertInLoop_n(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    assert n <= 100
    n -= 1"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
