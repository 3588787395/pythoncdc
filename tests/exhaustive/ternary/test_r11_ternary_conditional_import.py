import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryConditionalImport(ExhaustiveTestCase):
    """Bug R11 (new): conditional import + ternary in module-level code.

    原始:
        import sys
        json = __import__('json' if sys.version_info >= (3, 11) else 'simplejson')
    缺陷: ternary 作为 __import__ 的参数。cond_block 内含 LOAD_NAME sys +
         LOAD_ATTR version_info + LOAD_CONST (3, 11) + COMPARE_OP >=，
         merge 块 LOAD_CONST 'json'/'simplejson' + PUSH_NULL + LOAD_NAME
         __import__ + PRECALL 1 + CALL 1 + STORE_NAME json。可能暴露
         ternary 作为函数调用 arg 的归属冲突。
    """
    SOURCE_CODE = """import sys
json = __import__('json' if sys.version_info >= (3, 11) else 'simplejson')
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
