import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13TernaryThreeOrCond(ExhaustiveTestCase):
    # if 条件中三个三元表达式作 or 操作数：
    # if (a if c else b) or (d if e else f) or (g if h else i):
    #     pass
    # 字节码含三段独立三元 merge_block，分别由 cond c / e / h 选择 a/b、d/f、g/i，
    # 再由外层 or 短路（JUMP_IF_TRUE_OR_POP）连接。
    # 三个 TernaryRegion 共享 cond_block 链，反编译器需正确合并所有三元。
    SOURCE_CODE = """if (a if c else b) or (d if e else f) or (g if h else i):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
