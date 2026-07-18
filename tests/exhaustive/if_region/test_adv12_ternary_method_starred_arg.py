import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryMethodStarredArg(ExhaustiveTestCase):
    # if 条件中三元表达式作方法调用的 receiver，且方法调用含 starred 参数：
    # if (a if c else b).m(*args) > 0
    # 字节码含 LOAD_METHOD, BUILD_TUPLE/LOAD, PRECALL, CALL。
    SOURCE_CODE = """if (a if c else b).m(*args) > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
