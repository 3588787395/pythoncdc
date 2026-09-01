"""Dump disassembly + exception table for backtest.pyc handle_backtest_build.

Focus: (1) f-string BUILD_STRING region around the user_code assignment;
(2) the inner try: shutil.copy(...) region whose except handler is being dropped.
"""
import dis
import marshal
import types

PYC = r"F:\Downloads\pythoncdc-main\site-packages\IQCommon\backtest\backtest.pyc"

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)


def find(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find(const, name)
            if r is not None:
                return r
    return None


fn = find(code, 'handle_backtest_build')
print('=' * 70)
print('function:', fn.co_name, 'argcount=', fn.co_argcount,
      'vars=', fn.co_varnames)
print('exceptiontable:')
for entry in fn.co_exceptiontable:
    print('  ', entry)
print('=' * 70)
print('constants (string ones):')
for i, c in enumerate(fn.co_consts):
    if isinstance(c, str):
        print(f'  const[{i}] str: {c!r}')
    elif isinstance(c, types.CodeType):
        print(f'  const[{i}] <code {c.co_name}>')
    else:
        print(f'  const[{i}] {type(c).__name__}: {c!r}')
print('=' * 70)
dis.dis(fn)
