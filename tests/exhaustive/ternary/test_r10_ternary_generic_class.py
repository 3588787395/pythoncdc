import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryGenericClass(ExhaustiveTestCase):
    """Bug R10: typing.Generic + ternary — 字节码不一致。

    原始:
        from typing import Generic, TypeVar
        T = TypeVar('T')
        class C(Generic[T]):
            x: T = (a if c else b)
    缺陷: Generic[T] 基类（Subscript 节点）+ AnnAssign ternary body。
         Generic[T] 编译为 LOAD_NAME Generic + LOAD_NAME T + BINARY_SUBSCR
         作为 __build_class__ 的 base 参数；类体 AnnAssign ternary merge 块
         的 STORE_NAME x 与 Generic[T] 求值的栈帧共存于同一 class code
         object。R8 已测 AnnAssign ternary；R10 测 Generic + AnnAssign +
         ternary 变体。依「父引用子入口」：父 AnnAssign 通过 STORE_NAME x
         引用 ternary 子节点作为 value；ClassDef 通过 bases 引用 Generic[T]。
    """
    SOURCE_CODE = """from typing import Generic, TypeVar
T = TypeVar('T')
class C(Generic[T]):
    x: T = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
