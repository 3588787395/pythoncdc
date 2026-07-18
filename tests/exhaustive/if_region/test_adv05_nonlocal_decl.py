import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05NonlocalDecl(ExhaustiveTestCase):
    # if 体内 nonlocal 声明
    SOURCE_CODE = """def outer():
    x = 0
    def inner():
        if c:
            nonlocal x
            x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
