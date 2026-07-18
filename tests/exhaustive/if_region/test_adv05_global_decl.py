import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05GlobalDecl(ExhaustiveTestCase):
    # if 体内 global 声明
    SOURCE_CODE = """def f():
    if c:
        global g
        g = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
