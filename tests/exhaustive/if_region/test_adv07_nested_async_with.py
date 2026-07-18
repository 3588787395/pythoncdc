import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07NestedAsyncWith(ExhaustiveTestCase):
    # if 体内多层嵌套 async with: async with a: async with b:
    SOURCE_CODE = """async def f():
    if c:
        async with a:
            async with b:
                r = x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
