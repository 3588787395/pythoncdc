"""
L2两层嵌套穷举测试用例 (48项)

使用穷举法覆盖所有两层控制流嵌套组合：
- 外层: if / while / for / try / with / match (6种)
- 内层: if / while / for / try / with / match / ternary / boolop (8种)
- 总计: 6 × 8 = 48 种组合
"""

import ast
from .base import ControlFlowTestCase


def _make_source(outer, inner):
    templates = {
        ('if', 'if'): """def f(x, y):
    if x > 0:
        if y > 0:
            return 1
    return 0""",
        ('if', 'while'): """def f(n):
    if n > 0:
        while n > 0:
            n -= 1
    return n""",
        ('if', 'for'): """def f(items):
    if items:
        for x in items:
            print(x)""",
        ('if', 'try'): """def f(x):
    if x > 0:
        try:
            x += 1
        except:
            pass
    return x""",
        ('if', 'with'): """def f(fobj):
    if fobj:
        with fobj as f:
            f.read()""",
        ('if', 'match'): """def f(x):
    if x is not None:
        match x:
            case 1: return 'one'
            case _: return 'other'
    return 'none'""",
        ('if', 'ternary'): """def f(a, b, c):
    if a > 0:
        x = b if c else b + 1
    else:
        x = -1
    return x""",
        ('if', 'boolop'): """def f(a, b, c):
    if c:
        if a and b:
            return 1
    return 0""",
        ('while', 'if'): """def f(n):
    while n > 0:
        if n % 2 == 0:
            print(n)
        n -= 1""",
        ('while', 'while'): """def f(a, b):
    while a > 0:
        while b > 0:
            b -= 1
        a -= 1""",
        ('while', 'for'): """def f(seq):
    while seq:
        for x in seq:
            print(x)
        break""",
        ('while', 'try'): """def f(n):
    while n > 0:
        try:
            n -= 1
        except:
            break""",
        ('while', 'with'): """def f(file_list):
    while file_list:
        with open(file_list.pop()) as f:
            f.read()""",
        ('while', 'match'): """def f(stream):
    while stream:
        x = stream.pop()
        match x:
            case 0: break
            case _: print(x)""",
        ('while', 'ternary'): """def f(n):
    while n > 0:
        x = n if n % 2 else n // 2
        n -= 1""",
        ('while', 'boolop'): """def f(a, b):
    while a > 0 and b > 0:
        a -= 1
        b -= 1""",
        ('for', 'if'): """def f(items, threshold):
    for item in items:
        if item > threshold:
            return item
    return None""",
        ('for', 'while'): """def f(items, n):
    for item in items:
        while n > 0:
            n -= 1
            item += 1""",
        ('for', 'for'): """def f(matrix):
    for row in matrix:
        for cell in row:
            print(cell)""",
        ('for', 'try'): """def f(items):
    for item in items:
        try:
            int(item)
        except ValueError:
            continue""",
        ('for', 'with'): """def f(files):
    for name in files:
        with open(name) as f:
            f.read()""",
        ('for', 'match'): """def f(items):
    for x in items:
        match x:
            case 0: print('zero')
            case _: print(x)""",
        ('for', 'ternary'): """def f(items, flag):
    for item in items:
        x = item if flag else -item
        print(x)""",
        ('for', 'boolop'): """def f(items, a, b):
    for item in items:
        if a and b:
            item += 1""",
        ('try', 'if'): """def f(x):
    try:
        if x > 0:
            return 1
    except:
        pass
    return 0""",
        ('try', 'while'): """def f(n):
    try:
        while n > 0:
            n -= 1
    except:
        pass
    return n""",
        ('try', 'for'): """def f(items):
    try:
        for item in items:
            print(item)
    except:
        pass""",
        ('try', 'try'): """def f(x):
    try:
        try:
            x += 1
        except ValueError:
            x = 0
    except:
        x = -1
    return x""",
        ('try', 'with'): """def f(filepath):
    try:
        with open(filepath) as f:
            f.read()
    except:
        pass""",
        ('try', 'match'): """def f(x):
    try:
        match x:
            case 0: return 'zero'
            case _: return str(x)
    except:
        return 'error'""",
        ('try', 'ternary'): """def f(a, b, c):
    try:
        x = a if c else b
    except:
        x = None
    return x""",
        ('try', 'boolop'): """def f(a, b):
    try:
        if a and b:
            return 1
    except:
        pass
    return 0""",
        ('with', 'if'): """def f(fobj, threshold):
    with fobj as f:
        if f and threshold > 0:
            f.read()""",
        ('with', 'while'): """def f(fobj, n):
    with fobj as f:
        while n > 0:
            f.read()
            n -= 1""",
        ('with', 'for'): """def f(fobj, lines):
    with fobj as f:
        for line in lines:
            f.write(line)""",
        ('with', 'try'): """def f(fobj):
    with fobj as f:
        try:
            data = f.read()
        except:
            data = None
    return data""",
        ('with', 'with'): """def f(src, dst):
    with src as fin:
        with dst as fout:
            fout.write(fin.read())""",
        ('with', 'match'): """def f(fobj, x):
    with fobj as f:
        match x:
            case 0: f.read()
            case _: pass""",
        ('with', 'ternary'): """def f(fobj, flag, a, b):
    with fobj as f:
        x = a if flag else b
    return x""",
        ('with', 'boolop'): """def f(fobj, a, b):
    with fobj as f:
        if a and b:
            f.read()""",
        ('match', 'if'): """def f(x, threshold):
    match x:
        case int(n) if threshold > 0:
            if n > threshold:
                return n
        case _:
            return 0""",
        ('match', 'while'): """def f(x, n):
    match x:
        case 'loop':
            while n > 0:
                n -= 1
        case _:
            pass
    return n""",
        ('match', 'for'): """def f(x, items):
    match x:
        case 'process':
            for item in items:
                print(item)
        case _:
            pass""",
        ('match', 'try'): """def f(x):
    match x:
        case 'risky':
            try:
                risky_op()
            except:
                pass
        case _:
            pass""",
        ('match', 'with'): """def f(x, fobj):
    match x:
        case 'file':
            with fobj as f:
                f.read()
        case _:
            pass""",
        ('match', 'match'): """def f(x, y):
    match x:
        case 0:
            match y:
                case 0: return (0, 0)
                case _: return (0, 1)
        case _:
            return (-1, -1)""",
        ('match', 'ternary'): """def f(x, a, b, c):
    match x:
        case 0:
            result = a if c else b
        case _:
            result = -1
    return result""",
        ('match', 'boolop'): """def f(x, a, b):
    match x:
        case 0 if a and b:
            return 1
        case _:
            return 0""",
    }
    return templates.get((outer, inner), "")


def _make_test_name(outer, inner):
    name_map = {
        'if': 'If', 'while': 'While', 'for': 'For',
        'try': 'Try', 'with': 'With', 'match': 'Match',
        'ternary': 'Ternary', 'boolop': 'BoolOp',
    }
    return f"TestN2_{name_map[outer]}_{name_map[inner]}"


OUTER_TYPES = ['if', 'while', 'for', 'try', 'with', 'match']
INNER_TYPES = ['if', 'while', 'for', 'try', 'with', 'match', 'ternary', 'boolop']


def _generate_test_class(outer, inner):
    test_name = _make_test_name(outer, inner)
    source = _make_source(outer, inner)

    namespace = {
        'SOURCE_CODE': source,
    }

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")

    namespace['test_structure_correct'] = test_structure_correct
    return type(test_name, (ControlFlowTestCase,), namespace)


_classes = {}
for outer in OUTER_TYPES:
    for inner in INNER_TYPES:
        cls = _generate_test_class(outer, inner)
        _classes[cls.__name__] = cls
        globals()[cls.__name__] = cls


# 测试统计：总计48项
# outer=if  × inner=(if,while,for,try,with,match,ternary,boolop) = 8
# outer=while × inner=(if,while,for,try,with,match,ternary,boolop) = 8
# outer=for  × inner=(if,while,for,try,with,match,ternary,boolop) = 8
# outer=try  × inner=(if,while,for,try,with,match,ternary,boolop) = 8
# outer=with × inner=(if,while,for,try,with,match,ternary,boolop) = 8
# outer=match × inner=(if,while,for,try,with,match,ternary,boolop) = 8
# 48 项
