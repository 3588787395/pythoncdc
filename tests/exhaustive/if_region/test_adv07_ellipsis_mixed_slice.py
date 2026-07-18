import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv07EllipsisMixedSlice(ExhaustiveTestCase):
    # if 体内 Ellipsis 切片与常量混合: x[..., 0, ..., 1]
    SOURCE_CODE = """if c:
    r = x[..., 0, ..., 1]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
