import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07ListcompMultiIf(ExhaustiveTestCase):
    # if 体内 listcomp 多重 if 过滤: [x for x in y if x > 0 if x < 10]
    SOURCE_CODE = """if c:
    r = [x for x in y if x > 0 if x < 10]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
