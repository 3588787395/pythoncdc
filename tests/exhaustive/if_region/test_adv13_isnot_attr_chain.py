import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13IsnotAttrChain(ExhaustiveTestCase):
    # if 条件中 is not None 检查后访问属性并再次 is not None 检查：
    # if x is not None and x.field is not None:
    #     pass
    # 字节码 LOAD_NAME x / LOAD_CONST None / IS_OP 1 (is not)
    # / POP_JUMP_IF_FALSE
    # / LOAD_NAME x / LOAD_ATTR field / LOAD_CONST None / IS_OP 1
    # / POP_JUMP_IF_FALSE。
    # 同一变量 x 在 and 短路两侧均被使用，且第二段含 LOAD_ATTR。
    SOURCE_CODE = """if x is not None and x.field is not None:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
