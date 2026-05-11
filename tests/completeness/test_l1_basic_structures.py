#!/usr/bin/env python3
"""L1基础结构完备性测试 (52项)"""
import ast, sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tests.control_flow_matrix.base import ControlFlowTestCase

class TestL1BasicStructures(unittest.TestCase):
    def _decompile(self, src):
        from core.cfg import CFGBuilder, RegionASTGenerator
        from core.cfg.code_generator import CodeGenerator
        return CodeGenerator().generate(RegionASTGenerator(CFGBuilder().build(compile(src,'<test>','exec'))).generate())

    def _verify(self, src, *kws):
        d = self._decompile(src)
        ast.parse(d)
        for k in kws: self.assertIn(k, d)
        return d

    # L1.1 Basic (8)
    def test_L1_1_simple_assign(self):
        self._verify("x = 1", "=")

    def test_L1_2_augmented_assign(self):
        self._verify("x=0\nx+=1", "+=")

    def test_L1_3_multi_target_assign(self):
        self._verify("a=b=1", "a", "b")

    def test_L1_4_tuple_unpack(self):
        self._verify("a,b=(1,2)", "a", "b")

    def test_L1_5_expr_stmt(self):
        self._verify("def f():\n pass\nf()", "f()")

    def test_L1_6_return_value(self):
        self._verify("def f(x):\n return x", "return")

    def test_L1_7_return_none(self):
        self._verify("def f():\n return", "return")

    def test_L1_8_pass_stmt(self):
        self._verify("pass", "pass")

    # L1.2 Conditional (7)
    def test_L1_9_if_then(self):
        self._verify("x=5\nif x>0:\n print(x)", "if")

    def test_L1_10_if_else(self):
        self._verify("def a():pass\ndef b():pass\nx=5\nif x>0:a()\nelse:b()", "if","else")

    def test_L1_11_if_elif(self):
        self._verify("def a():pass\ndef b():pass\nx=5\nif x>0:a()\nelif x<0:b()", "if","elif")

    def test_L1_12_if_elif_else(self):
        self._verify("x=5\nif x>0:a=1\nelif x<0:a=2\nelse:a=3", "if","elif","else")

    def test_L1_13_multi_elif(self):
        self._verify("x=2\nif x==1:a=1\nelif x==2:a=2\nelif x==3:a=3\nelse:a=0", "if","elif")

    def test_L1_14_nested_if(self):
        self._verify("x=True\ny=True\nif x:\n if y: z=1", "if")

    def test_L1_15_nested_if_else(self):
        self._verify("def a():pass\ndef b():pass\nx=True\nif x:\n if y:a()\n else:b()", "if","else")

    # L1.3 Loop (18) - Basic
    def test_L1_16_for_loop(self):
        self._verify("for i in range(10):\n print(i)", "for")

    def test_L1_17_while_true(self):
        self._verify("x=0\nwhile True:\n x+=1\n if x>100: break", "while","break")

    def test_L1_18_for_else(self):
        self._verify("for i in range(5): x=i\nelse: print('done')", "for","else")

    def test_L1_19_while_else(self):
        self._verify("x=0\nwhile x<10: x+=1\nelse: print('done')", "while","else")

    # L1.3 Loop - break/continue
    def test_L1_20_for_break(self):
        self._verify("for i in range(10):\n if i==5: break", "for","break")

    def test_L1_21_for_continue(self):
        self._verify("for i in range(10):\n if i%2: continue\n print(i)", "for","continue")

    def test_L1_22_for_break_continue(self):
        self._verify("for i in range(10):\n if i==5:break\n if i%2:continue", "for","break","continue")

    def test_L1_23_while_break(self):
        self._verify("x=0\nwhile x<10:\n x+=1\n if x==5:break", "while","break")

    def test_L1_24_while_continue(self):
        self._verify("x=0\nwhile x<10:\n x+=1\n if x%2:continue", "while","continue")

    def test_L1_25_while_break_continue(self):
        self._verify("x=0\nwhile x<10:\n x+=1\n if x==5:break\n if x%2:continue", "while","break","continue")

    def test_L1_26_for_else_break(self):
        self._verify("for i in range(10):\n if i==5:break\nelse: print('no')", "for","else","break")

    def test_L1_27_while_else_break(self):
        self._verify("x=0\nwhile x<10:\n x+=1\n if x==5:break\nelse: print('no')", "while","else","break")

    # L1.3 Loop - nested
    def test_L1_28_nested_for_for(self):
        self._verify("for i in range(3):\n for j in range(4): print(i,j)", "for")

    def test_L1_29_nested_for_while(self):
        self._verify("for i in range(5):\n j=0\n while j<10: j+=1", "for","while")

    def test_L1_30_nested_while_for(self):
        self._verify("x=0\nwhile x<10:\n for i in range(5): x+=i", "while","for")

    def test_L1_31_nested_while_while(self):
        self._verify("x=0\ny=0\nwhile x<10:\n while y<10: y+=1\n x+=1", "while")

    def test_L1_32_for_if_break(self):
        self._verify("for i in range(10):\n if i>5: break", "for","if","break")

    def test_L1_33_while_if_break(self):
        self._verify("x=0\nwhile x<10:\n x+=1\n if x>5:break", "while","if","break")

    # L1.4 Exception (13)
    def test_L1_34_try_except(self):
        self._verify("try:\n x=1/0\nexcept:\n x=0", "try","except")

    def test_L1_35_try_except_typed(self):
        self._verify("try:\n int('abc')\nexcept ValueError:\n x=0", "try","ValueError")

    def test_L1_36_try_multi_except(self):
        self._verify("try:\n int('abc')\nexcept (ValueError,TypeError):\n x=0", "ValueError","TypeError")

    def test_L1_37_try_except_else(self):
        self._verify("try:\n x=1/0\nexcept:\n pass\nelse:\n print('ok')", "try","except","else")

    def test_L1_38_try_finally(self):
        self._verify("def c():pass\ntry: x=1\nfinally: c()", "try","finally")

    def test_L1_39_try_except_finally(self):
        self._verify("def c():pass\ntry:x=1/0\nexcept:x=0\nfinally:c()", "try","except","finally")

    def test_L1_40_try_except_else_finally(self):
        self._verify("def c():pass\ntry:x=1/0\nexcept:x=0\nelse:print('ok')\nfinally:c()", "try","except","else","finally")

    def test_L1_41_except_as(self):
        self._verify("try:\n x=1/0\nexcept Exception as e:\n print(e)", "except","as")

    def test_L1_42_nested_try(self):
        self._verify("try:\n try:x=1/0\n except:pass\nexcept:pass", "try","except")

    def test_L1_43_except_break(self):
        self._verify("def f(x):pass\nfor x in[1,-1]:\n try:f(x)\n except:\n  if x<0:break", "for","try","break")

    def test_L1_44_except_return(self):
        self._verify("def g():\n try:x=1/0\n except:return None", "try","return")

    def test_L1_45_finally_return(self):
        self._verify("def g():\n x=1\n try:pass\n finally:return x", "finally","return")

    def test_L1_46_reraise(self):
        self._verify("try:\n x=1/0\nexcept:\n raise", "try","raise")

    # L1.5 With (6)
    def test_L1_47_with_simple(self):
        self._verify("class F:\n def read(self):return ''\n def __enter__(self):return self\n def __exit__(s,a):pass\nf=F()\nwith f as d:d.read()", "with","as")

    def test_L1_48_without_as(self):
        self._verify("class L:\n def __enter__(self):pass\n def __exit__(s,a):pass\ndef d():pass\nl=L()\nwith l:d()", "with")

    def test_L1_49_multi_context_with(self):
        self._verify("class C:\n def __enter__(self):return self\n def __exit__(s,a):pass\na=C();b=C()\nwith a as x,b as y:pass", "with","as")

    def test_L1_50_nested_with(self):
        self._verify("class C:\n def __enter__(self):return self\n def __exit__(s,a):pass\na=C();b=C()\nwith a:\n with b:pass", "with")

    def test_L1_51_with_try_cross(self):
        self._verify("class C:\n def __enter__(self):return self\n def __exit__(s,a):pass\na=C()\nwith a:\n try:x=1/0\n except:x=0", "with","try")

    def test_L1_52_with_break_continue(self):
        self._verify("class C:\n def __enter__(self):return self\n def __exit__(s,a):pass\nc=C()\nfor x in[1,-1]:\n with c:\n  if x<0:break", "for","with","break")


if __name__ == '__main__':
    unittest.main()
