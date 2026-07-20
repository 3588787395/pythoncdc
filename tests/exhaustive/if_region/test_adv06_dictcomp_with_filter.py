import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06DictcompWithFilter(ExhaustiveTestCase):
    # if 体内 dictcomp with filter (双 for 子句 + if)
    SOURCE_CODE = """if c:
    r = {k: v for k, v in items if k > 0}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
