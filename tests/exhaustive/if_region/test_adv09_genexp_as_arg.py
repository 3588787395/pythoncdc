import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09GenexpAsArg(ExhaustiveTestCase):
    # if 体内生成器表达式作函数唯一参数 sum(x for x in range(10))
    SOURCE_CODE = """if c:
    s = sum(x for x in range(10))"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
