import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10NestedTernaryReturn(ExhaustiveTestCase):
    # if 体内嵌套三元在 return return a if c else (b if d else e)
    SOURCE_CODE = """def f():
    if c:
        return a if cond1 else (b if cond2 else e)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
