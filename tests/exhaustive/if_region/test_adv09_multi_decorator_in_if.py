import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09MultiDecoratorInIf(ExhaustiveTestCase):
    # if 体内多装饰器叠加
    SOURCE_CODE = """if c:
    @decorator1
    @decorator2
    def f():
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
