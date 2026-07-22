import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryMethodChainArgMiddle(ExhaustiveTestCase):
    """Bug R17-01: s.replace('a', 'b').split((a if c else b)) — method chain with arg in middle。

    原始:
        s.replace('a', 'b').split((a if c else b))
    缺陷: 中间方法 replace('a','b') 带 args，紧接 .split(ternary)。代码注释
         明确说明「带 args 的中间方法调用（如 s.method(x).split(ternary)）
         留待 R14+」，_detect_ternary_context 中 LOAD_METHOD method chain
         处理仅识别 0-arg 中间调用 (PRECALL 紧跟 LOAD_METHOD)。带 args 时
         obj chain 重建中断，反编译丢失 replace('a','b') 和外层 .split()，
         退化为 s.replace(ternary)。
    """
    SOURCE_CODE = """s.replace('a', 'b').split((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
