import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05StarredAssign(ExhaustiveTestCase):
    # if 体内 star expression 作赋值目标 a, *b = ...
    SOURCE_CODE = """if c:
    a, *b = d"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
