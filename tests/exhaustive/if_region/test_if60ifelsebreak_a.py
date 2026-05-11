import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF60Ifelsebreak_a(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(10):
    if a > i:
        a = i
    else:
        break"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
