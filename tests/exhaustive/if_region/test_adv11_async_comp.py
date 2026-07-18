import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11AsyncComp(ExhaustiveTestCase):
    # if 体内 async for 在 list comprehension 中（包裹在 async def 内）
    SOURCE_CODE = """async def f():
    if c:
        x = [i async for i in y]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
