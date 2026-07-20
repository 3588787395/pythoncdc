import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv02AwaitSecondOr(ExhaustiveTestCase):
    SOURCE_CODE = """async def f():
    if x or await g():
        return 1
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
