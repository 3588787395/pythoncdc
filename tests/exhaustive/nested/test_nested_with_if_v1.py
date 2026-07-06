import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedWithIf_v1(ExhaustiveTestCase):
    SOURCE_CODE = """with open('f') as f:
    if x:
        y = 1
    else:
        y = 2"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
