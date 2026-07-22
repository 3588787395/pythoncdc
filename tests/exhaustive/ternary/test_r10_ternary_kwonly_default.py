import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryKwonlyDefault(ExhaustiveTestCase):
    """Bug R10: ternary in default of kwonly arg — 字节码不一致。

    原始:
        def f(*args, x=(a if c else b)):
            pass
    缺陷: ternary 作为 kwonly 参数 x 的默认值。kwonly 默认值通过
         BUILD_CONST_KEY_MAP 而非 BUILD_TUPLE 构建（与 R6-err6 已修复的
         lambda x, *, y=10 模式相关）。ternary merge 块的栈输出作为
         BUILD_CONST_KEY_MAP 的 value，KW_NAMES + LOAD_CONST ('x',) +
         ternary merge + BUILD_CONST_KEY_MAP + MAKE_FUNCTION。
         依「父引用子入口」：父 FunctionDef 通过 MAKE_FUNCTION 引用
         FunctionObject；FunctionObject.kw_defaults 通过 BUILD_CONST_KEY_MAP
         引用 ternary 子节点作为 value。
    """
    SOURCE_CODE = """def f(*args, x=(a if c else b)):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
