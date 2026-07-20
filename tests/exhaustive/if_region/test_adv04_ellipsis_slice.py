import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04EllipsisSlice(ExhaustiveTestCase):
    # Ellipsis 切片（a[..., 0]）
    SOURCE_CODE = """if c:
    x = a[..., 0]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
