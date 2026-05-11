import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF42Ifinfor_n(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(10):
    if n > i:
        n = i"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
