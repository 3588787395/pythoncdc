# Round13 family fix probe: verify delimiter selection + Tier-2 fallback.
# Mirrors REAL46-004: expr fragment contains triple-double-quote string with real newline.
import sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.code_generator import CFGCodeGenerator

gen = CFGCodeGenerator()

def render(values):
    node = {'type': 'JoinedStr', 'values': values}
    return gen._generate_joined_str_from_dict(node)

def FV(expr_dict, conv=None, spec=None):
    v = {'type': 'FormattedValue', 'value': expr_dict, 'conversion': conv if conv is not None else -1}
    if spec is not None:
        v['format_spec'] = spec
    return v

def Const(s):
    return {'type': 'Constant', 'value': s}

def Name(n):
    return {'type': 'Name', 'id': n, 'ctx': {'type': 'Load'}}

results = []

# T1: REAL46-004 pattern - triple-double-quoted string with real newline in expr
src = render([FV(Name('name'), 1), Const(' member mismatch:\n      '),
              FV({'type': 'Call',
                  'func': {'type': 'Attribute', 'value': Const('\n      '), 'attr': 'join', 'ctx': {'type': 'Load'}},
                  'args': [Name('failed_member')], 'keywords': []}, 2)])
results.append(('T1 newline+tripleDQ in expr', src))

# T2: plain f-string, no quotes in expr -> single-quote delim (byte-identity with old)
src2 = render([Const('a '), FV(Name('x')), Const(' b')])
results.append(('T2 plain', src2))

# T3: expr with single quotes only -> double delim
src3 = render([Const('x='), FV({'type': 'Compare', 'left': Name('a'), 'ops': [{'type': 'Eq'}],
                                'comparators': [Const('tick')]}), Const('!')])
results.append(('T3 single-quote in expr', src3))

# T4: expr with both quote types, no newline -> triple-single delim
src4 = render([FV({'type': 'Compare', 'left': Const('a'), 'ops': [{'type': 'Eq'}],
                   'comparators': [Const("b'c")]}, 1)])
results.append(('T4 both quotes', src4))

# T5: expr with backslash -> Tier 2 concat
src5 = render([Const('p='), FV({'type': 'BinOp', 'left': Name('x'), 'op': {'type': 'Add'},
                                'right': Const('a\\b')}, 1), Const('!')])
results.append(('T5 backslash -> Tier2', src5))

# T6: expr with newline, no quotes -> triple-single delim (was broken single)
src6 = render([Const('msg='), FV({'type': 'Attribute', 'value': Const('line1\nline2'),
                                  'attr': 'strip', 'ctx': {'type': 'Load'}})])
results.append(('T6 newline no quotes', src6))

# T7: expr containing ''' sequence + both quotes -> Tier 2
src7 = render([FV({'type': 'BinOp', 'left': Const("'''x'''"), 'op': {'type': 'Add'},
                   'right': Const('a"b')}, 1)])
results.append(('T7 triple-single conflict -> Tier2', src7))

# T8: literal with quote run adjacent to triple-single delim
src8 = render([Const("it's a 'test'"), FV(Name('y'))])
results.append(('T8 literal quotes + triple delim', src8))

for tag, src in results:
    print(f'--- {tag}')
    print(repr(src))
    # compile check with 3.11
    try:
        compile(src, '<probe>', 'eval')
        # semantic check: eval with namespace
        ns = {'name': 'SPAM', 'failed_member': ['m1', 'm2'], 'x': 5, 'a': 'tick',
              'y': 42, 'p': None}
        # T5 needs x defined
        val = eval(src, ns)
        print(f'  COMPILE_OK eval={val!r}')
    except SyntaxError as e:
        print(f'  SYNTAX_FAIL: {e}')
    except Exception as e:
        print(f'  COMPILE_OK eval_error: {type(e).__name__}: {e}')
