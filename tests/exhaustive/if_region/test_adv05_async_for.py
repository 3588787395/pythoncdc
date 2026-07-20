import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05AsyncFor(ExhaustiveTestCase):
    # if 体内 async for
    SOURCE_CODE = """async def f():
    if c:
        async for x in g():
            y = x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
