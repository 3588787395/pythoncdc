import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06AwaitDictElem(ExhaustiveTestCase):
    # if 体内 await 作 dict 字面量 value 元素
    SOURCE_CODE = """async def f():
    if c:
        r = {k: await g(), m: await h()}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
