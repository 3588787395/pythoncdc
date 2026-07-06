"""L3三层深度嵌套测试 (18项)

覆盖Python控制流的三层嵌套关键组合模式：
L3.1: for->for->for    L3.2: for->while->for     L3.3: while->if->for
L3.4: for->if->while   L3.5: try->for->if        L3.6: with->try->for
L3.7: for->if->try     L3.8: while->try->if       L3.9: for->if(break)->for
L3.10: while->if(break)->while  L3.11: try->for(break)->if
L3.12: for->try->if(continue)  L3.13: while->for->try(except)
L3.14: if->for->while  L3.15: for->with->try      L3.16: while->if->with
L3.17: try->with->for  L3.18: match->if->for
"""
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


class TestL31ForForFor(ControlFlowTestCase):
    """L3.1: for->for->for"""
    SOURCE_CODE = "for i in range(3):\n    for j in range(3):\n        for k in range(3):\n            x=i*9+j*3+k"

    def test_structure(self):
        d,t=_dc(self);self.assertEqual(len([n for n in ast.walk(t) if isinstance(n,ast.For)]),3)


class TestL32ForWhileFor(ControlFlowTestCase):
    """L3.2: for->while->for"""
    SOURCE_CODE = "for i in range(5):\n    j=0\n    while j<i:\n        for k in range(j): pass\n        j+=1"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.While))


class TestL33WhileIfFor(ControlFlowTestCase):
    """L3.3: while->if->for"""
    SOURCE_CODE = "x=0\nwhile x<20:\n    x+=1\n    if x%2==0:\n        for i in range(x): pass"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.While));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.For))


class TestL34ForIfWhile(ControlFlowTestCase):
    """L3.4: for->if->while"""
    SOURCE_CODE = "for i in range(15):\n    if i>5:\n        j=0\n        while j<3: j+=1"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.While))


class TestL35TryForIf(ControlFlowTestCase):
    """L3.5: try->for->if"""
    SOURCE_CODE = "try:\n    for item in data:\n        if item.ok(): use(item)\nexcept Error: fail()"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Try));self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.If))


class TestL36WithTryFor(ControlFlowTestCase):
    """L3.6: with->try->for"""
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nwith c as ctx:\n    try:\n        for x in items: process(x)\n    except E: skip()"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.With));self.assertIsNotNone(self.find_node(t,ast.Try));self.assertIsNotNone(self.find_node(t,ast.For))


class TestL37ForIfTry(ControlFlowTestCase):
    """L3.7: for->if->try"""
    SOURCE_CODE = "for item in items:\n    if item.valid:\n        try: process(item)\n        except VErr: log(item)"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.Try))


class TestL38WhileTryIf(ControlFlowTestCase):
    """L3.8: while->try->if"""
    SOURCE_CODE = "x=0\nwhile x<30:\n    x+=1\n    try:\n        val=get(x)\n        if val>0: use(val)\n    except Err: pass"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.While));self.assertIsNotNone(self.find_node(t,ast.Try));self.assertIsNotNone(self.find_node(t,ast.If))


class TestL39ForIfBreakFor(ControlFlowTestCase):
    """L3.9: for->if(break)->for"""
    SOURCE_CODE = "for row in matrix:\n    found=False\n    for cell in row:\n        if cell==target:\n            found=True\n            break\n    if found: return cell"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Break));self.assertGreaterEqual(len([n for n in ast.walk(t) if isinstance(n,ast.For)]),2)


class TestL310WhileIfBreakWhile(ControlFlowTestCase):
    """L3.10: while->if(break)->while"""
    SOURCE_CODE = "outer=0\nwhile outer<50:\n    outer+=1\n    inner=0\n    while inner<outer:\n        inner+=1\n        if inner==5: break"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Break));self.assertGreaterEqual(len([n for n in ast.walk(t) if isinstance(n,ast.While)]),2)


class TestL311TryForBreakIf(ControlFlowTestCase):
    """L3.11: try->for(break)->if"""
    SOURCE_CODE = "try:\n    for i in range(100):\n        if i==limit: break\n        work(i)\n    if done: finish()\nexcept StopErr: abort()"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Try));self.assertIsNotNone(self.find_node(t,ast.Break));self.assertIsNotNone(self.find_node(t,ast.If))


class TestL312ForTryIfContinue(ControlFlowTestCase):
    """L3.12: for->try->if(continue)"""
    SOURCE_CODE = "for item in batch:\n    try:\n        check(item)\n        if item.skip(): continue\n        save(item)\n    except CheckErr: discard(item)"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.Try));self.assertIsNotNone(self.find_node(t,ast.Continue))


class TestL313WhileForTryExcept(ControlFlowTestCase):
    """L3.13: while->for->try(except)"""
    SOURCE_CODE = "x=0\nwhile x<40:\n    x+=1\n    for y in range(x):\n        try: op(y)\n        except OpErr: fix(y)"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.While));self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.Try))


class TestL314IfForWhile(ControlFlowTestCase):
    """L3.14: if->for->while"""
    SOURCE_CODE = "if mode=='fast':\n    for i in range(100):\n        j=0\n        while j<i: j+=1\nelse: slow()"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.While))


class TestL315ForWithTry(ControlFlowTestCase):
    """L3.15: for->with->try"""
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nfor item in items:\n    with c as lock:\n        try: safe_op(item,lock)\n        except LockErr: release(lock)"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.For));self.assertIsNotNone(self.find_node(t,ast.With));self.assertIsNotNone(self.find_node(t,ast.Try))


class TestL316WhileIfWith(ControlFlowTestCase):
    """L3.16: while->if->with"""
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nx=0\nwhile x<60:\n    x+=1\n    if need_lock(x):\n        with c as l: do(x,l)"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.While));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.With))


class TestL317TryWithFor(ControlFlowTestCase):
    """L3.17: try->with->for"""
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\ntry:\n    with c as res:\n        for entry in entries: write(entry,res)\nexcept IOError: cleanup()"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Try));self.assertIsNotNone(self.find_node(t,ast.With));self.assertIsNotNone(self.find_node(t,ast.For))


class TestL318MatchIfFor(ControlFlowTestCase):
    """L3.18: match->if->for"""
    SOURCE_CODE = "cmd='search'\nmatch cmd:\n    case 'search':\n        if query:\n            for result in db.search(query): show(result)\n    case 'list': list_all()\n    case _: help()"

    def test_structure(self):
        d,t=_dc(self);self.assertIsNotNone(self.find_node(t,ast.Match));self.assertIsNotNone(self.find_node(t,ast.If));self.assertIsNotNone(self.find_node(t,ast.For))


if __name__ == '__main__':
    import unittest
    unittest.main()
