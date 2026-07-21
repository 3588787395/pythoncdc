import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryTypevarBound(ExhaustiveTestCase):
    """Bug R10: typing.TypeVar + ternary bound — 字节码不一致。

    原始:
        from typing import TypeVar
        T = TypeVar('T', bound=(A if c else B))
    缺陷: TypeVar 调用的 bound= 参数是 ternary。KW_NAMES + LOAD_CONST
         'bound' + ternary merge + BUILD_TUPLE + KWAPPS + PRECALL + CALL。
         ternary merge 块的栈输出作为 bound 关键字参数，可能暴露 ternary
         consumer 识别冲突（与 R9-06/10/12 kwarg call 模式相关）。
         依「父引用子入口」：父 Assign 通过 STORE_NAME T 引用 TypeVar
         Call 节点；TypeVar Call 通过 cond_block 入口 + merge_block 的
         KW_NAMES 引用 ternary 子节点作为 bound 关键字参数值。
    """
    SOURCE_CODE = """from typing import TypeVar
T = TypeVar('T', bound=(A if c else B))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
