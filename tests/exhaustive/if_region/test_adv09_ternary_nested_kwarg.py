import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09TernaryNestedKwarg(ExhaustiveTestCase):
    # if 体内嵌套三元作关键字参数 f(x=a if c else b, y=d if e else g)
    SOURCE_CODE = """if c:
    f(x=a if cond else b, y=d if e else g)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
