import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryMaxDefault(ExhaustiveTestCase):
    """Bug R12 (new): max(iterable, default=ternary) — 字节码不一致。

    原始:
        max(x, default=(a if c else b))
    缺陷: ternary 作为 max 的 keyword 参数 default=ternary。KW_NAMES +
         LOAD_CONST ('default',) + ternary merge + PRECALL + CALL 2。
         cond_block preload 含 PUSH_NULL + LOAD_GLOBAL max + LOAD_NAME x，
         ternary merge 块的栈输出作为 KW_NAMES 对应的 kwarg value。
         与 _try_build_ternary_kwarg_call 单 kwarg 场景类似但 func 是 builtin。
    """
    SOURCE_CODE = """max(x, default=(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
