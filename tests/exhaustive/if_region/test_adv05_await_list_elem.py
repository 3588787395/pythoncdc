import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05AwaitListElem(ExhaustiveTestCase):
    # if 体内 await 作列表元素
    SOURCE_CODE = """async def f():
    if c:
        r = [await g(), await h()]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
