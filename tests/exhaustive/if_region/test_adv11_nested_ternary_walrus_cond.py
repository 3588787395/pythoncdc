import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11NestedTernaryWalrusCond(ExhaustiveTestCase):
    # if 条件中海象赋值的嵌套三元表达式 if (n := (a if b else c if d else e)):
    SOURCE_CODE = """if (n := (a if b else c if d else e)):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
