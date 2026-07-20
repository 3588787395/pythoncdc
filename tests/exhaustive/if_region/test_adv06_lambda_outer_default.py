import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06LambdaOuterDefault(ExhaustiveTestCase):
    # if 体内 lambda 默认参数引用外部变量
    SOURCE_CODE = """if c:
    f = lambda x=a, y=b: x + y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
