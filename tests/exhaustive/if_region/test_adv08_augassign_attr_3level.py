import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08AugassignAttr3Level(ExhaustiveTestCase):
    # if 体内 augassign 三层属性 a.b.c.d += 1
    SOURCE_CODE = """if c:
    a.b.c.d += 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
