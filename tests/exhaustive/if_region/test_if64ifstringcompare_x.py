import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF64Ifstringcompare_x(ExhaustiveTestCase):
    SOURCE_CODE = """if x == "hello":
    x = "world"
"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
