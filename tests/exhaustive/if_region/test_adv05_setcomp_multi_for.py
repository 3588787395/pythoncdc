import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05SetcompMultiFor(ExhaustiveTestCase):
    # if 体内 setcomp 多 for 子句
    SOURCE_CODE = """if c:
    r = {x + y for x in a for y in b}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
