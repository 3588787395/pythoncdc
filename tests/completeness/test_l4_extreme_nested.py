"""L4四层极限深度嵌套测试 (5项)"""
import ast, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tests.control_flow_matrix.base import ControlFlowTestCase

def _dc(self):
    from core.cfg import CFGBuilder, RegionASTGenerator
    from core.cfg.code_generator import CodeGenerator
    try:
        code = compile(self.SOURCE_CODE, '<test>', 'exec')
    except SyntaxError as e:
        if "'return' outside function" in str(e):
            indented = '\n'.join('    ' + line for line in self.SOURCE_CODE.split('\n'))
            self.source_code = f"def _wrap():\n{indented}\n_wrap()\n"
            code = compile(self.source_code, '<test>', 'exec')
        else:
            raise
    cfg = CFGBuilder().build(code)
    gen = RegionASTGenerator(cfg).generate()
    src = CodeGenerator().generate(gen)
    tree = ast.parse(src)
    return src, tree

class TestL41ForForForFor(ControlFlowTestCase):
    """L4.1: for->for->for->for"""
    SOURCE_CODE = "result=[]\nfor i in range(2):\n    for j in range(2):\n        for k in range(2):\n            for l in range(2):\n                result.append(i*8+j*4+k*2+l)"
    def test_structure(self):
        d,t=_dc(self);self.assertEqual(len([n for n in ast.walk(t) if isinstance(n,ast.For)]),4)

class TestL42ForIfWhileTry(ControlFlowTestCase):
    """L4.2: for->if->while->try"""
    SOURCE_CODE = "for batch in batches:\n    if batch.active:\n        idx=0\n        while idx<len(batch):\n            try: process(batch[idx])\n            except Err: skip(batch[idx])\n            idx+=1"
    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.While));self.assertIsNotNone(self.find_node(t,ast.Try))

class L43WhileIfForWith(ControlFlowTestCase):
    """L4.3: while->if->for->with"""
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nx=0\nwhile x<10:\n    x+=1\n    if x%2==0:\n        for y in range(x):\n            with c as ctx: work(x,y,ctx)"
    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.While));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.With))

class L44TryForIfWhile(ControlFlowTestCase):
    """L4.4: try->for->if->while"""
    SOURCE_CODE = "try:\n    for group in groups:\n        if group.valid:\n            i=0\n            while i<group.count:\n                use(group.items[i])\n                i+=1\nexcept FailErr: cleanup()"
    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Try));self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.While))

class L45ForIfBreakWhileTry(ControlFlowTestCase):
    """L4.5: for->if(break)->while->try"""
    SOURCE_CODE = "for stage in stages:\n    if stage.cancelled(): break\n    attempt=0\n    while attempt<max_retries:\n        attempt+=1\n        try: run_stage(stage)\n        except RetryErr: continue\n        break"
    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Break));self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.While));self.assertIsNotNone(self.find_node(t,ast.Try))

if __name__ == '__main__':
    import unittest
    unittest.main()
