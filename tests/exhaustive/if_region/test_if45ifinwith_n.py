import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF45Ifinwith_n(ExhaustiveTestCase):
    SOURCE_CODE = """with open("f") as f:
    if n > 0:
        n = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
