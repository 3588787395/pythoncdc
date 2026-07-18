import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08AttrAugassignChainMethodRhs(ExhaustiveTestCase):
    # if 体内 augassign 属性目标 + 方法调用右值 a.b += f(c).g(d)
    SOURCE_CODE = """if c:
    a.b += f(c).g(d)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
