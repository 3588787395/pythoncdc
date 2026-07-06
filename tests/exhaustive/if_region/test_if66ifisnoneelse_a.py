import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF66Ifisnoneelse_a(ExhaustiveTestCase):
    SOURCE_CODE = """if a is None:
    a = 0
else:
    a = a + 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
