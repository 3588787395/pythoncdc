import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11WhileWalrusOnly(ExhaustiveTestCase):
    # if 体内 while 条件中只有 walrus while (x := f()):
    SOURCE_CODE = """if c:
    while (x := f()):
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
