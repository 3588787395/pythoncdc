import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAs03AssertInIf_a(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    assert a < 100
    result = a"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
