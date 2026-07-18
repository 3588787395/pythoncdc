import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08LambdaWithComplexDefault(ExhaustiveTestCase):
    # if 体内 lambda 默认参数含复杂表达式 lambda x=a+b, y=c*2: x+y
    SOURCE_CODE = """if c:
    f = lambda x=a + b, y=c * 2: x + y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
