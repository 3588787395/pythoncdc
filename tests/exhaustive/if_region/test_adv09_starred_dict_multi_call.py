import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09StarredDictMultiCall(ExhaustiveTestCase):
    # if 体内调用中带多个 dict 解包 + 位置参数 f(a, b, **c, **d)
    SOURCE_CODE = """if c:
    f(a, b, **c, **d)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
