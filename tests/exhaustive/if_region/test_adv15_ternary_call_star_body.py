import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryCallStarBody(ExhaustiveTestCase):
    # if 体内调用含 *(三元) 星号解包参数：
    # if c:
    #     f(*(a if x else b))
    # 字节码 PUSH_NULL / LOAD_NAME f / 含三元 merge_block（cond=x
    # 选择 a / b）/ BUILD_TUPLE 1 / CALL_FUNCTION_EX 1 / POP_TOP。
    # 反编译器在三元 merge 与 CALL_FUNCTION_EX 的 *args 栈位归约时
    # 丢失星号，产出 f(a if x else b)（普通位置参数调用），字节码
    # 由 CALL_FUNCTION_EX 变为 PRECALL/CALL，指令序列不匹配。
    SOURCE_CODE = """if c:
    f(*(a if x else b))"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
