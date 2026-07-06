import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF82Ifnotindict_n(ExhaustiveTestCase):
    SOURCE_CODE = """d = {1: 2}
if n not in d:
    d[n] = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
