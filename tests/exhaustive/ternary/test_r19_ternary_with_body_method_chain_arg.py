import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryWithBodyMethodChainArg(ExhaustiveTestCase):
    """Bug R19-04: with body 内 cm.process(t1).finalize() — ternary 作方法链参数位于 with body。

    原始:
        with ctx() as cm:
            cm.process(a if c else b).finalize()
    缺陷: with body 内表达式 cm.process(t1).finalize() —— ternary 是中间方法
         process(...) 的位置参数，外层 .finalize() 调用消费 process 的返回值。
         R17 method_arg_then_attr 测过 `obj.method(t1).other` (非 with body)，
         R17 method_chain_arg_middle 测过 `s.replace('a','b').split(t1)`。
         本用例 ternary 在 with body 内且外层是方法链 .process(t1).finalize()：
         ternary merge 块的 PRECALL+CALL (process) + LOAD_METHOD finalize +
         PRECALL+CALL (finalize) 消费链与 with body 块归属冲突，反编译丢失
         外层 .finalize() 调用，退化为 `cm.process(a if c else b)`。
    """
    SOURCE_CODE = """with ctx() as cm:
    cm.process(a if c else b).finalize()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
