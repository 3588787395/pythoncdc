import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06StarredCallInBody(ExhaustiveTestCase):
    # if 体内星号表达式作函数参数
    SOURCE_CODE = """if c:
    r = f(*args, **kwargs)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
