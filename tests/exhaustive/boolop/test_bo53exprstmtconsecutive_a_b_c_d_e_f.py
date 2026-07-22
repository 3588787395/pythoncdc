import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBO53ExprStmtConsecutive_a_b_c_d_e_f(ExhaustiveTestCase):
    # 两个连续的「表达式语句」BoolOp（结果被 POP_TOP 丢弃，无 STORE 边界）：
    #   a or b or c
    #   d or e or f
    # 此前 Bug: 两个表达式语句的 BoolOp 链跨越 POP_TOP 语句边界合并成一个
    # BoolOpRegion，且第一表达式被误建 IfRegion，反编译为
    #   if (a or b or c or d or e or e):
    #       f
    # 修复: (1) _detect_boolop_short_circuit_chain 的 fall-through 扩展
    #          不应并入首指令为 POP_TOP 的块（语句边界）；
    #       (2) generate() containment 豁免用共享块首指令判据（POP_TOP/
    #           STORE_*）替代 value_target，覆盖表达式语句；
    #       (3) _identify_conditional_regions 值上下文 BoolOp 入口在 merge
    #          首指令为 POP_TOP 时跳过 IfRegion 创建。
    SOURCE_CODE = """a or b or c
d or e or f"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
