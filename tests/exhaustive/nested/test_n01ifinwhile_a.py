import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN01IfInWhile_a(ExhaustiveTestCase):
    SOURCE_CODE = """while a > 0:
    if a > 5:
        a -= 2
    else:
        a -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
