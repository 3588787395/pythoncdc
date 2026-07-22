import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryVersionDefinition(ExhaustiveTestCase):
    """Bug R11 (new): __version__ definition + ternary.

    原始:
        import sys
        __version__ = ('1.0' if sys.version_info >= (3, 11) else '0.9')
    缺陷: module 级 __version__ 赋值的右值是 ternary，ternary 的 test 子表达式
         包含属性访问 + 比较 (sys.version_info >= (3, 11))。cond_block 内含
         LOAD_NAME sys + LOAD_ATTR version_info + LOAD_CONST (3, 11) +
         COMPARE_OP >=，merge 块 LOAD_CONST '1.0'/'0.9' + STORE_NAME __version__。
         可能暴露比较表达式 + 元组常量在 ternary cond_block 的归属冲突。
    """
    SOURCE_CODE = """import sys
__version__ = ('1.0' if sys.version_info >= (3, 11) else '0.9')
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
