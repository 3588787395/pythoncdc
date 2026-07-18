import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryKwarg(ExhaustiveTestCase):
    # if 体内三元作函数关键字参数 f(x=1 if c else 2)
    SOURCE_CODE = """if c:
    f(x=1 if cond else 2)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
