import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06AwaitCallArg(ExhaustiveTestCase):
    # if 体内 await 作函数调用参数 f(await g(), x)
    SOURCE_CODE = """async def f():
    if c:
        r = h(await g(), x)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
