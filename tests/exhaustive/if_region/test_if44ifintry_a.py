import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF44Ifintry_a(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    if a > 0:
        a = 1
except:
    a = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
