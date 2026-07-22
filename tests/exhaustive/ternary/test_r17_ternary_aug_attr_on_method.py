import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryAugAttrOnMethod(ExhaustiveTestCase):
    """Bug R17-08: (a if c else b).method().attr += 1 — aug assign attr on ternary method chain。

    原始:
        (a if c else b).method().attr += 1
    缺陷: ternary 调用 .method() 后取 .attr 做 augmented assignment (+= 1)。
         R16 attr_aug_assign 测过 (a if c else b).attr += 1，但中间多一层
         .method() 调用后 LOAD_ATTR attr + LOAD + BINARY_OP + STORE_ATTR
         消费链未被 _try_build_ternary_store_assign 处理，反编译退化为
         `(a if c else b).method()`，丢失 .attr += 1，指令数严重不匹配 (15 vs 10)。
    """
    SOURCE_CODE = """(a if c else b).method().attr += 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
