import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05AsyncWith(ExhaustiveTestCase):
    # if 体内 async with
    SOURCE_CODE = """async def f():
    if c:
        async with g() as x:
            y = x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
