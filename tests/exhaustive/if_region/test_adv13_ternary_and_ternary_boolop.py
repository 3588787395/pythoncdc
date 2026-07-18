import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13TernaryAndTernaryBoolop(ExhaustiveTestCase):
    # if 条件中两个三元表达式作 and 操作数：
    # if (a if c else b) and (d if e else f):
    #     pass
    # 字节码含两段独立三元 merge_block，分别用 LOAD_NAME a/b 与 LOAD_NAME d/f
    # 由 cond c / e 选择，再由外层 and 短路（JUMP_IF_FALSE_OR_POP）连接。
    # 两个 TernaryRegion 共享 cond_block，但归属不同的 and 分支。
    SOURCE_CODE = """if (a if c else b) and (d if e else f):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
