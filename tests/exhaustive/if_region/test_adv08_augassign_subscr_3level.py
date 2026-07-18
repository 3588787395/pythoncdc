import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08AugassignSubscr3Level(ExhaustiveTestCase):
    # if 体内 augassign 嵌套下标三层 d[k1][k2][k3] += 1
    SOURCE_CODE = """if c:
    d[k1][k2][k3] += 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
