import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08WhileElseInIf(ExhaustiveTestCase):
    # if 体内嵌套 while-else
    SOURCE_CODE = """if c:
    while x > 0:
        x -= 1
    else:
        r = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
