import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07AsyncWithMultiCtx(ExhaustiveTestCase):
    # if 体内 async with 多上下文管理器: async with a as x, b as y:
    SOURCE_CODE = """async def f():
    if c:
        async with a as x, b as y:
            r = x + y"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
