import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04TupleUnpackBody(ExhaustiveTestCase):
    # if 体内元组解包赋值（SWAP 路径：a, b = c, d）
    SOURCE_CODE = """if c:
    a, b = d, e"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
