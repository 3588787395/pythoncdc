import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs02AssertMsg_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(s):
    assert isinstance(s, str), f"expected str, got {type(s).__name__}"
"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
