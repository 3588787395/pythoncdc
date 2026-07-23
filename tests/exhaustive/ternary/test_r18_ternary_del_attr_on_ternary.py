import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryDelAttrOnTernary(ExhaustiveTestCase):
    """Bug R18-10: del (a if c else b).x — del attr 直接作用在 ternary 上。

    原始:
        del (a if c else b).x
    缺陷: DELETE_ATTR 的对象表达式是 ternary。R8 del_attr_chain 测过
         `del obj[ternary].attr` (subscript 含 ternary 后取 attr)，
         R8 del_subscript_both 测过 `del (ternary)[ternary]`。
         本用例 ternary 直接是 DELETE_ATTR 的对象：ternary merge 块的
         LOAD_ATTR x + DELETE_ATTR 消费链未被 _try_build_ternary_store_assign
         处理 (它处理 STORE_ATTR/STORE_SUBSCR，不处理 DELETE_ATTR)。
         反编译退化为破碎的多段 POP_TOP 表达式，字节码指令数不匹配 (7 vs 10)。
    """
    SOURCE_CODE = """del (a if c else b).x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
