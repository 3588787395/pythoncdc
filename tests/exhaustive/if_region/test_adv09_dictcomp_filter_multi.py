import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09DictCompFilterMulti(ExhaustiveTestCase):
    # if 体内字典推导式带 if 过滤 {k: v for k, v in items if k > 0}
    SOURCE_CODE = """if c:
    r = {k: v for k, v in items if k > 0}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
