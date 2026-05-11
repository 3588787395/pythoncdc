import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF81Ifelifcontinue_x(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(10):
    if x > i:
        x = i
    elif x == 5:
        continue"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
