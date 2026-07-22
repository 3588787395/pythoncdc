import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryDataclassDefaultFactory(ExhaustiveTestCase):
    """Bug R10: dataclass field default_factory lambda ternary — 字节码不一致。

    原始:
        from dataclasses import dataclass, field
        @dataclass
        class C:
            x: int = field(default_factory=lambda: (a if c else b))
    缺陷: R9-10 已知 frozen dataclass field 默认值 ternary 失败。R10 测
         default_factory lambda body 含 ternary 变体：ternary 在 lambda
         code object 内（独立区域），field(default_factory=...) 调用栈帧
         PUSH_NULL + LOAD_NAME field + LOAD_CONST lambda_code + MAKE_FUNCTION
         + KW_NAMES + LOAD_CONST default_factory + PRECALL + CALL + STORE_NAME x
         与 AnnAssign 的 value 表达式归属可能冲突。依「嵌套即抽象节点」：
         lambda 作为 default_factory 的参数在父 field() Call 中作为单个抽象节点。
    """
    SOURCE_CODE = """from dataclasses import dataclass, field
@dataclass
class C:
    x: int = field(default_factory=lambda: (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
