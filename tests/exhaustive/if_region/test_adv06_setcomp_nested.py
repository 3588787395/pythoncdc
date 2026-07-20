import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06SetcompNested(ExhaustiveTestCase):
    # if 体内嵌套 set 推导式 {x for x in a if x > 0}
    SOURCE_CODE = """if c:
    r = {x + 1 for x in a if x > 0}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
