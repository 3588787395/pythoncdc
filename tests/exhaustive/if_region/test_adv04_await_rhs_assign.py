import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04AwaitRhsAssign(ExhaustiveTestCase):
    # await 作赋值右值（async 函数内 if 体）
    SOURCE_CODE = """async def f():
    if c:
        x = await g()
    return x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
