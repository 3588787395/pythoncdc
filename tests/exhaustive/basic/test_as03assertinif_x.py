import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs03AssertInIf_x(ExhaustiveTestCase):
    SOURCE_CODE = """if x is not None:
    assert x >= 0
    value = x"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
