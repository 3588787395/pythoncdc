import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09WalrusAttr(ExhaustiveTestCase):
    # if 体内 walrus 在属性取值中 r = obj.(x := f()) - 实际为 r = (x := f()).attr
    SOURCE_CODE = """if c:
    r = (x := f()).attr"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
