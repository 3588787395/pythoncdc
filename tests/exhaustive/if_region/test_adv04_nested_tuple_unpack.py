import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04NestedTupleUnpack(ExhaustiveTestCase):
    # 嵌套元组解包（(a, (b, c)) = (1, (2, 3))）
    SOURCE_CODE = """if c:
    (a, (b, cc)) = (1, (2, 3))"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
