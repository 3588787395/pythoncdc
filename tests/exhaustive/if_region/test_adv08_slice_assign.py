import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08SliceAssign(ExhaustiveTestCase):
    # if 体内 slice 作赋值目标 a[1:3] = b
    SOURCE_CODE = """if c:
    a[1:3] = b"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
