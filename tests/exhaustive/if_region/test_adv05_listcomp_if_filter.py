import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv05ListcompIfFilter(ExhaustiveTestCase):
    # if 体内 listcomp 带 if 过滤
    SOURCE_CODE = """if c:
    r = [x for x in s if x > 0]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
