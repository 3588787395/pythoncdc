import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryCallArgAndKwarg(ExhaustiveTestCase):
    # if 体内三元同时作位置参数和关键字参数 f(a if c else b, x=d if e else g)
    SOURCE_CODE = """if c:
    f(a if cond else b, x=d if e else g)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
