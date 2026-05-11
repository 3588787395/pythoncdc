import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF06NestedIf_a_3(ExhaustiveTestCase):
    SOURCE_CODE = """if a > 0:
    if a > 3:
        a = 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
