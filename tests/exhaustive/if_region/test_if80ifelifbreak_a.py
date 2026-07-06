import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF80Ifelifbreak_a(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(10):
    if a > i:
        a = i
    elif a == 5:
        break"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
