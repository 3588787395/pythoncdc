import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11LambdaDecorator(ExhaustiveTestCase):
    # if 体内 lambda 作为装饰器
    SOURCE_CODE = """if c:
    @lambda f: None
    def g():
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
