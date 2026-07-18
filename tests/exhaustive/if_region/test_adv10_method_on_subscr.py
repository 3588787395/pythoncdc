import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10MethodOnSubscr(ExhaustiveTestCase):
    # if 体内下标上的方法调用 lst[0].method()
    SOURCE_CODE = """if c:
    x = lst[0].method()"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
