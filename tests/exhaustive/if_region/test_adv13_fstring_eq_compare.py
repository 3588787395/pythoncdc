import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13FstringEqCompare(ExhaustiveTestCase):
    # if 条件中 f-string 与字符串常量相等比较：
    # if f"{x}" == "hello":
    #     pass
    # 字节码 LOAD_NAME x / FORMAT_VALUE 0 / LOAD_CONST 'hello' / COMPARE_OP ==
    # 后 POP_JUMP_IF_FALSE。
    # f-string 在 FORMAT_VALUE 指令中产生，参与 COMPARE_OP 后整体作为 if 条件。
    SOURCE_CODE = '''if f"{x}" == "hello":
    pass'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
