import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09DocstringInIf(ExhaustiveTestCase):
    # if 体内字符串字面量（隐式 docstring）
    SOURCE_CODE = """if c:
    "docstring"
    x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
