import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09DecoratorWithArgsInIf(ExhaustiveTestCase):
    # if 体内带参数装饰器
    SOURCE_CODE = """if c:
    @decorator(arg=1)
    def f():
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
