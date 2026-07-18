import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10LambdaTernaryDefault(ExhaustiveTestCase):
    # if 体内 lambda 默认参数为三元表达式
    SOURCE_CODE = """if c:
    f = lambda x=(a if cond else b): x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
