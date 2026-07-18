import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09WalrusInAssertMsgSubscr(ExhaustiveTestCase):
    # if 体内 walrus 在 assert 消息含下标 assert x, d[(n := f())]
    SOURCE_CODE = """if c:
    assert x, d[(n := f())]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
