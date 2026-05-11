import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedWithIf_v2(ExhaustiveTestCase):
    SOURCE_CODE = """with open('f') as f:
    if a:
        b = 1
    else:
        b = 2"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
