import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryDataclassPostInit(ExhaustiveTestCase):
    """Bug R10: dataclass __post_init__ body 含 ternary — 字节码不一致。

    原始:
        from dataclasses import dataclass
        @dataclass
        class C:
            x: int = 0
            def __post_init__(self):
                self.x = a if c else b
    缺陷: R9-10 已知 frozen dataclass field 默认值 ternary 失败。R10 测
         __post_init__ 方法体内 ternary 赋值变体：ternary 在 __post_init__
         code object 内，merge 块的 STORE_ATTR x 与 dataclass 装饰器调用栈
         可能在跨 code object 时误归属。依「父引用子入口」：父 Assign
         通过 merge_block 的 STORE_ATTR 引用 ternary 子节点作为右值。
    """
    SOURCE_CODE = """from dataclasses import dataclass
@dataclass
class C:
    x: int = 0
    def __post_init__(self):
        self.x = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
