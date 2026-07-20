import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryMethodChain(ExhaustiveTestCase):
    # if 条件中三元表达式作方法链调用的 receiver：
    # if (a if c else b).m().n() > 0
    # 字节码含 LOAD_METHOD, PRECALL, CALL, LOAD_ATTR/LOAD_METHOD（方法链）。
    SOURCE_CODE = """if (a if c else b).m().n() > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
