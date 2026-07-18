import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TernaryDecorator(ExhaustiveTestCase):
    # if 体内 decorator 为三元表达式
    SOURCE_CODE = """if c:
    @(dec1 if c2 else dec2)
    def f():
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
