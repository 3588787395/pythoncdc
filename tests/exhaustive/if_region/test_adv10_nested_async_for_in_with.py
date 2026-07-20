import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10NestedAsyncForInWith(ExhaustiveTestCase):
    # if 体内 async with 嵌套 async for
    SOURCE_CODE = """async def f():
    if c:
        async with ctx() as x:
            async for i in x:
                print(i)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
