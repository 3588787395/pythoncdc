import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedIfTry_v1(ExhaustiveTestCase):
    SOURCE_CODE = """if x:
    try:
        y = 1
    except:
        y = 2"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
