import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08ChaincmpMethodCall(ExhaustiveTestCase):
    # if 条件含链式比较中段带方法调用 a.f() < b.g() < c.h()
    SOURCE_CODE = """if a.f() < b.g() < c.h():
    r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
