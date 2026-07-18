import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11DecoratorLambdaWithArgs(ExhaustiveTestCase):
    # if 体内带参数的 lambda 作为装饰器
    SOURCE_CODE = """if c:
    @(lambda f: lambda *a, **k: f(*a, **k))
    def g():
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
