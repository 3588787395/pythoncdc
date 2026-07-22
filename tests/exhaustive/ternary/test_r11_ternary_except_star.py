import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryExceptStar(ExhaustiveTestCase):
    """Bug R9-08 (re-verify in R11): except* PEP 654 + ternary handler body.

    原始:
        try:
            pass
        except* E as e:
            x = (a if c else b)
    缺陷: except* handler body 含 ternary 赋值。PUSH_EXC_INFO + CHECK_EG_MATCH +
         COPY 路径与 ternary merge 块的 STORE_NAME x 在同一 handler body。
    """
    SOURCE_CODE = """try:
    pass
except* E as e:
    x = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
