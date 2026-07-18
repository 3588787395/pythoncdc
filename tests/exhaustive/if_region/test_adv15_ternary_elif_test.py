import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryElifTest(ExhaustiveTestCase):
    # elif 的测试条件本身为三元表达式：
    # if a:
    #     pass
    # elif (b if c else d):
    #     pass
    # 字节码 POP_JUMP_IF_FALSE（cond=a）/ LOAD_NAME c
    # / POP_JUMP_IF_FALSE（跳到 d 分支）/ LOAD_NAME b
    # / POP_JUMP_IF_FALSE（跳到 elif body 后）...
    # 反编译器将三元测试条件错误地分解为多层 elif 链：
    # elif c: if b: pass / elif d: pass，语义不等价
    # （原始语义是 (b if c else d) 整体作 elif 条件）。
    SOURCE_CODE = """if a:
    pass
elif (b if c else d):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
