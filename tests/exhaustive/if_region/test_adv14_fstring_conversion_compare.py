import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14FstringConversionCompare(ExhaustiveTestCase):
    # f-string conversion (!r) 比较：
    # if f"{a!r}" == "x":
    #     pass
    # 字节码 LOAD_NAME a / FORMAT_VALUE 2（conversion='r'）
    # / LOAD_CONST 'x' / COMPARE_OP == / POP_JUMP_IF_FALSE。
    # FORMAT_VALUE 的 conversion flag 为 2 表示 repr，反编译需生成 !r。
    SOURCE_CODE = '''if f"{a!r}" == "x":
    pass'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
