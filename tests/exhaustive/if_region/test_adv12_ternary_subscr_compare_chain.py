import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernarySubscrCompareChain(ExhaustiveTestCase):
    # if 条件中三元作下标且整体在链式比较中段：
    # if 0 < d[a if c else b] < 10
    # 字节码含 BINARY_SUBSCR（ternary 作下标）+ SWAP/COPY（链式比较）。
    SOURCE_CODE = """if 0 < d[a if c else b] < 10:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
