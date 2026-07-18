import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06NestedTernaryBody(ExhaustiveTestCase):
    # if 体内多层嵌套三元 a if b else c if d else e 作赋值右值
    SOURCE_CODE = """if c:
    z = a if b else cc if d else e"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
