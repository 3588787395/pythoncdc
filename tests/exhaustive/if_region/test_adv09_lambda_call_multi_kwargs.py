import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09LambdaCallWithMultiKwargs(ExhaustiveTestCase):
    # if 体内 lambda 调用含多个关键字参数
    SOURCE_CODE = """if c:
    r = (lambda x, y: x + y)(x=1, y=2)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
