import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN07IfInTry_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    if a > 0:
        pass
except IndexError:
    pass"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
