import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08WalrusAssertMsg(ExhaustiveTestCase):
    # if 体内 assert 带 walrus 消息 assert x, (n := f())
    SOURCE_CODE = """if c:
    assert x, (n := f())"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
