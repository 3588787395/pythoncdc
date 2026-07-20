import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07AwaitWalrusValue(ExhaustiveTestCase):
    # if 体内 await 作 walrus 值: r = (n := await g())
    SOURCE_CODE = """async def f():
    if c:
        r = (n := await g())
    return r"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
