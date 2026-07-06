import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs02AssertMsg_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    assert len(items) > 0, "items must not be empty"
"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
