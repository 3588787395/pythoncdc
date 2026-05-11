import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN02IfInFor_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(10):
    if x > 5:
        continue"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
