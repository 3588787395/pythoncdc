import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06AwaitInSubscr(ExhaustiveTestCase):
    # if 体内 await 作下标 d[await g()]
    SOURCE_CODE = """async def f():
    if c:
        r = d[await g()]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
