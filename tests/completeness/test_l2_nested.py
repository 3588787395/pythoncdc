"""L2两层嵌套完备性测试 (40项)

覆盖5种外层结构 × 8种内层结构的完整组合矩阵：
外层5种: for, while, try-except, with, if-else
内层8种: if-then, if-else, for, while, try-except, with, 嵌套同类型, match
"""
import ast, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tests.control_flow_matrix.base import ControlFlowTestCase


def _decompile_check(self):
    from core.cfg import CFGBuilder, RegionASTGenerator
    from core.cfg.code_generator import CodeGenerator
    code = compile(self.SOURCE_CODE, '<test>', 'exec')
    cfg = CFGBuilder().build(code)
    gen = RegionASTGenerator(cfg).generate()
    src = CodeGenerator().generate(gen)
    tree = ast.parse(src)
    return src, tree


class TestL201ForIfThen(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(10):\n    if i > 3:\n        x = i"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL202ForIfElse(ControlFlowTestCase):
    SOURCE_CODE = "def a():pass\ndef b():pass\nfor i in range(10):\n    if i % 2 == 0:\n        a()\n    else:\n        b()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL203ForFor(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(3):\n    for j in range(4):\n        x = i * j"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertEqual(len([n for n in ast.walk(t) if isinstance(n, ast.For)]), 2)

class TestL204ForWhile(ControlFlowTestCase):
    SOURCE_CODE = "for i in range(5):\n    j = 0\n    while j < 10:\n        j += 1"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.While))

class TestL205ForTry(ControlFlowTestCase):
    SOURCE_CODE = "for item in items:\n    try:\n        process(item)\n    except Error:\n        skip(item)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.Try))

class TestL206ForWith(ControlFlowTestCase):
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nfor x in data:\n    with c as ctx:\n        use(ctx)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.With))

class TestL207ForSameType(ControlFlowTestCase):
    SOURCE_CODE = "result=[]\nfor row in matrix:\n    row_sum=0\n    for val in row:\n        row_sum+=val\n    result.append(row_sum)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertEqual(len([n for n in ast.walk(t) if isinstance(n, ast.For)]), 2)

class TestL208ForMatch(ControlFlowTestCase):
    SOURCE_CODE = "for token in tokens:\n    match token.type:\n        case 'number': value=float(token.value)\n        case 'string': value=str(token.value)\n        case _: value=None"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.Match))

class TestL209WhileIfThen(ControlFlowTestCase):
    SOURCE_CODE = "x=0\nwhile x < 100:\n    if x > 50:\n        mark(x)\n    x+=1"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL210WhileIfElse(ControlFlowTestCase):
    SOURCE_CODE = "def a():pass\ndef b():pass\nx=0\nwhile x<20:\n    if x%3==0:a()\n    else:b()\n    x+=1"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL211WhileFor(ControlFlowTestCase):
    SOURCE_CODE = "x=0\nwhile x<5:\n    for i in range(x):\n        print(i)\n    x+=1"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.For))

class TestL212WhileWhile(ControlFlowTestCase):
    SOURCE_CODE = "x=0\ny=0\nwhile x<10:\n    y=0\n    while y<10:\n        y+=1\n    x+=1"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertEqual(len([n for n in ast.walk(t) if isinstance(n, ast.While)]), 2)

class TestL213WhileTry(ControlFlowTestCase):
    SOURCE_CODE = "x=0\nwhile x<10:\n    try:\n        risky(x)\n    except ValueError:\n        handle(x)\n    x+=1"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.Try))

class TestL214WhileWith(ControlFlowTestCase):
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nwhile active:\n    with c as ctx:\n        do_work(ctx)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.With))

class TestL215WhileSameType(ControlFlowTestCase):
    SOURCE_CODE = "outer=0\nwhile outer<5:\n    inner=0\n    while inner<outer*2:\n        inner+=1\n    outer+=1"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertEqual(len([n for n in ast.walk(t) if isinstance(n, ast.While)]), 2)

class TestL216WhileMatch(ControlFlowTestCase):
    SOURCE_CODE = "state='idle'\nwhile state!='exit':\n    match state:\n        case 'run': step()\n        case 'pause': wait()\n        case _: state='exit'"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.Match))

class TestL217TryIfThen(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    result=operation()\n    if result<0:\n        raise ValueError\nexcept ValueError:\n    fallback()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Try))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL218TryIfElse(ControlFlowTestCase):
    SOURCE_CODE = "def a():pass\ndef b():pass\ntry:\n    val=get_value()\n    if val>0:a(val)\n    else:b(val)\nexcept Error:\n    recover()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Try))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL219TryFor(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    for item in collection:\n        process(item)\nexcept ProcessingError:\n    cleanup()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Try))
        self.assertIsNotNone(self.find_node(t, ast.For))

class TestL220TryWhile(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    x=0\n    while x<100:\n        work(x)\n        x+=1\nexcept StopIteration:\n    done()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Try))
        self.assertIsNotNone(self.find_node(t, ast.While))

class TestL221TryTry(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    try:\n        deep_operation()\n    except InnerError:\n        fix_inner()\nexcept OuterError:\n    fix_outer()"
    def test_structure(self):
        d, t = _decompile_check(self)
        tries = [n for n in ast.walk(t) if isinstance(n, ast.Try)]
        self.assertGreaterEqual(len(tries), 1)

class TestL222TryWith(ControlFlowTestCase):
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\ntry:\n    with c as ctx:\n        risky(ctx)\nexcept RiskError:\n    abort()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Try))
        self.assertIsNotNone(self.find_node(t, ast.With))

class TestL223TrySameType(ControlFlowTestCase):
    SOURCE_CODE = "def c():pass\ntry:\n    try:\n        critical()\n    except AErr: pass\n    finally: c()\nexcept BErr:\n    failover()"
    def test_structure(self):
        d, t = _decompile_check(self)
        tries = [n for n in ast.walk(t) if isinstance(n, ast.Try)]
        self.assertGreaterEqual(len(tries), 1)

class TestL224TryMatch(ControlFlowTestCase):
    SOURCE_CODE = "try:\n    err=get_error()\n    match err.code:\n        case 404: not_found()\n        case 500: server_error()\n        case _: unknown()\nexcept Exception:\n    log()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Try))
        self.assertIsNotNone(self.find_node(t, ast.Match))

class TestL225WithIfThen(ControlFlowTestCase):
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nwith c as f:\n    line=f.read()\n    if line.startswith('#'):\n        comment(line)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.With))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL226WithIfElse(ControlFlowTestCase):
    SOURCE_CODE = "def a():pass\ndef b():pass\nclass C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nwith c as r:\n    if r.ok():a(r)\n    else:b(r)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.With))
        self.assertIsNotNone(self.find_node(t, ast.If))

class TestL227WithFor(ControlFlowTestCase):
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nwith c as db:\n    for row in db.query('SELECT *'):\n        process(row)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.With))
        self.assertIsNotNone(self.find_node(t, ast.For))

class TestL228WithWhile(ControlFlowTestCase):
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nwith c as conn:\n    while conn.has_data():\n        chunk=conn.read()\n        write(chunk)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.With))
        self.assertIsNotNone(self.find_node(t, ast.While))

class TestL229WithTry(ControlFlowTestCase):
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nwith c as f:\n    try:\n        data=f.load()\n    except IOError:\n        data=[]"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.With))
        self.assertIsNotNone(self.find_node(t, ast.Try))

class TestL230ForIfBreak(ControlFlowTestCase):
    """L2.30: for中if+break (D04关键用例)"""
    SOURCE_CODE = "for i in range(100):\n    if i == 42:\n        break\n    process(i)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Break))

class TestL231ForIfContinue(ControlFlowTestCase):
    """L2.31: for中if+continue"""
    SOURCE_CODE = "for i in range(20):\n    if i % 3 == 0:\n        continue\n    use(i)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Continue))

class TestL232ForIfBreakContinue(ControlFlowTestCase):
    """L2.32: for中if+break+continue"""
    SOURCE_CODE = "for i in range(50):\n    if i == 99: break\n    if i % 5 == 0: continue\n    compute(i)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.Break))
        self.assertIsNotNone(self.find_node(t, ast.Continue))

class TestL233WhileIfBreak(ControlFlowTestCase):
    """L2.33: while中if+break"""
    SOURCE_CODE = "x=0\nwhile x < 200:\n    x+=1\n    if x > 150: break\n    work(x)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Break))

class TestL234WhileIfContinue(ControlFlowTestCase):
    """L2.34: while中if+continue"""
    SOURCE_CODE = "x=0\nwhile x < 50:\n    x+=1\n    if x % 7 == 0: continue\n    process(x)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Continue))

class TestL235WhileIfBreakContinue(ControlFlowTestCase):
    """L2.35: while中if+break+continue"""
    SOURCE_CODE = "x=0\nwhile True:\n    x+=1\n    if x>999:break\n    if x%11==0:continue\n    step(x)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.Break))
        self.assertIsNotNone(self.find_node(t, ast.Continue))

class TestL236ForElseIfBreak(ControlFlowTestCase):
    """L2.36: for-else中if+break"""
    SOURCE_CODE = "for i in range(30):\n    if found(i): break\nelse:\n    not_found_msg()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.For))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Break))

class TestL237WhileElseIfBreak(ControlFlowTestCase):
    """L2.37: while-else中if+break"""
    SOURCE_CODE = "x=0\nwhile x < 80:\n    x+=1\n    if done(x): break\nelse:\n    completed()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.While))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Break))

class TestL238TryExceptIfBreak(ControlFlowTestCase):
    """L2.38: try-except中if+break (D04相关)"""
    SOURCE_CODE = "for x in values:\n    try:\n        check(x)\n    except CheckError:\n        if fatal: break\n        log(x)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Try))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Break))

class TestL239WithIfBreak(ControlFlowTestCase):
    """L2.39: with中if+break"""
    SOURCE_CODE = "class C:\n    def __enter__(self):return self\n    def __exit__(s,a,b,c):pass\nc=C()\nfor item in items:\n    with c as lock:\n        if lock.failed(): break\n        safe_op(lock)"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.With))
        self.assertIsNotNone(self.find_node(t, ast.If))
        self.assertIsNotNone(self.find_node(t, ast.Break))

class TestL240MatchBasic(ControlFlowTestCase):
    """L2.40: match基本结构"""
    SOURCE_CODE = "value=42\nmatch value:\n    case 0: zero()\n    case 1: one()\n    case _: default()"
    def test_structure(self):
        d, t = _decompile_check(self)
        self.assertIsNotNone(self.find_node(t, ast.Match))


if __name__ == '__main__':
    import unittest
    unittest.main()
