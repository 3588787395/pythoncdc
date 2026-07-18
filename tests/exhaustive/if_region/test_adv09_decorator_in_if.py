import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09DecoratorInIf(ExhaustiveTestCase):
    # if 体内 @decorator 装饰函数
    SOURCE_CODE = """if c:
    @decorator
    def f():
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
