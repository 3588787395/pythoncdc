import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10AwaitTernary(ExhaustiveTestCase):
    # if 体内 await 三元表达式 await (a if c else b)
    SOURCE_CODE = """async def f():
    if c:
        x = await (a if cond else b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
