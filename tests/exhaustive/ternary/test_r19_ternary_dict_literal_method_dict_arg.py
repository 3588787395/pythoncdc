import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryDictLiteralMethodDictArg(ExhaustiveTestCase):
    """Bug R19-14: {1:2}.update({(t1): 3}) — dict literal 方法调用，参数是含 ternary key 的 dict。

    原始:
        {1: 2}.update({(a if c else b): 3})
    缺陷: dict literal `{1: 2}` 调用 `.update(...)`，参数是另一个 dict literal
         `{(t1): 3}` —— ternary 是参数 dict 的 key。R15 dict_literal_method 测过
         `{}.get((ternary))` (ternary 直接作 .get 的位置参数)。本用例 ternary 是
         .update 参数 dict 内部的 key：外层 BUILD_MAP (参数 dict) 消费 ternary
         merge 块栈顶 (value 3) 与次栈顶 (key t1)，再被外层 LOAD_METHOD update +
         PRECALL+CALL 消费，反编译退化为 `{}.update({a if c else b: 3})`，丢失
         外层 dict literal 的常量键值对 `{1: 2}`，字节码指令数不匹配 (15 vs 13)。
    """
    SOURCE_CODE = """{1: 2}.update({(a if c else b): 3})
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
