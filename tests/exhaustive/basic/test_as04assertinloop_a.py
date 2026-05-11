import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs04AssertInLoop_a(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(10):
    assert i >= 0
    result = i * 2"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
