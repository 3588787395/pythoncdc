import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv06BytesFormat(ExhaustiveTestCase):
    # if 体内 bytes 操作 b'%s' % x
    SOURCE_CODE = """if c:
    z = b'%s:%d' % (s, n)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
