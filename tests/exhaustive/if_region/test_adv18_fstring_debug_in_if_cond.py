import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18FstringDebugInIfCond(ExhaustiveTestCase):
    # if 条件中含 f-string debug `=`（Python 3.8+）：
    # if f"{x=}" == "x=10":
    #     r = 'match'
    # elif f"{y=}" == "y=20":
    #     r = 'match_y'
    # else:
    #     r = 'no_match'
    # 字节码 LOAD_CONST "x=" / FORMAT_VALUE 4 (REPR) / BUILD_STRING / COMPARE_OP
    # / 反编译器在 if 条件中含 f-string `=` debug 时易丢失 `=` 标记或
    # 错识别 FORMAT_VALUE 的 repr 模式。
    SOURCE_CODE = """if f"{x=}" == "x=10":
    r = 'match'
elif f"{y=}" == "y=20":
    r = 'match_y'
else:
    r = 'no_match'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
