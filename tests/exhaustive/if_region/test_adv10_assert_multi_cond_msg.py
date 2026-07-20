import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10AssertMultiCondMsg(ExhaustiveTestCase):
    # if 体内 assert 多条件 + msg assert a > 0 and b > 0, "msg"
    SOURCE_CODE = """if c:
    assert a > 0 and b > 0, "msg" """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
