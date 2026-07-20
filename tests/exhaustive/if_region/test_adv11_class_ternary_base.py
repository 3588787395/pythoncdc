import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ClassTernaryBase(ExhaustiveTestCase):
    # if 体内 class 的基类为三元表达式 class C(A if c2 else B):
    SOURCE_CODE = """if c:
    class C(A if c2 else B):
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
