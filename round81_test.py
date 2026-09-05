import sys, os, types, marshal, dis, io, json, textwrap
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs, _normalize_argval

pyc_path = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/utils/__init__.pyc'

decompiled_source = decompile_pyc(pyc_path)

with open(pyc_path, 'rb') as f:
    f.read(16)
    original_code = marshal.load(f)

def extract_code_objects(code_obj, prefix=''):
    results = []
    name = prefix + code_obj.co_name if prefix else code_obj.co_name
    results.append((name, code_obj))
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            results.extend(extract_code_objects(const, sub_prefix))
    return results

original_funcs = extract_code_objects(original_code)
recompiled_code = compile(decompiled_source, '<decompiled>', 'exec')
recompiled_funcs = extract_code_objects(recompiled_code)

orig_dict = {name: code for name, code in original_funcs}
recomp_dict = {name: code for name, code in recompiled_funcs}

total = len(orig_dict)
matched = 0
mismatches = []

for name in orig_dict:
    if name not in recomp_dict:
        mismatches.append((name, 'MISSING in recompiled', None))
        continue
    result = compare_bytecode(orig_dict[name], recomp_dict[name])
    if result['match']:
        matched += 1
    else:
        mismatches.append((name, 'MISMATCH', result))

def format_instr(instr):
    argval = instr.argval
    if isinstance(argval, types.CodeType):
        argval = '<code object {}>'.format(argval.co_name)
    elif isinstance(argval, str) and (argval.endswith('.py') or argval.endswith('.pyc')) and ('/' in argval or '\\' in argval):
        argval = os.path.basename(argval)
    argrepr = instr.argrepr
    return '{:>4d} {:<40s} {}'.format(instr.offset, instr.opname, argrepr)

# Build the mismatched function source
def extract_func_source(source, func_name, is_method=False):
    lines = source.split('\n')
    in_func = False
    indent_level = 0
    func_lines = []
    search_name = func_name.split('.')[-1] if '.' in func_name else func_name
    
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if not in_func:
            if stripped.startswith('def {}('.format(search_name)):
                in_func = True
                indent_level = len(line) - len(stripped)
                func_lines.append(line)
                continue
        if in_func:
            if not stripped:
                func_lines.append(line)
                continue
            current_indent = len(line) - len(stripped)
            if current_indent <= indent_level and stripped:
                break
            func_lines.append(line)
    
    return '\n'.join(func_lines)

# Get wrapper function source too
wrapper_source = extract_func_source(decompiled_source, 'wrapper')

# Now build the comprehensive report
R = []
R.append('=' * 80)
R.append('ROUND81 TEST REPORT: Bytecode Comparison for __init__.pyc')
R.append('=' * 80)
R.append('')
R.append('PYC File: {}'.format(pyc_path))
R.append('Python Version: {}'.format(sys.version))
R.append('Decompiled source length: {} chars'.format(len(decompiled_source)))
R.append('')
R.append('')

R.append('=' * 80)
R.append('SECTION 1: Summary')
R.append('=' * 80)
R.append('')
R.append('Total code objects (functions): {}'.format(total))
R.append('Matched (semantically equivalent): {}'.format(matched))
R.append('Mismatched: {}'.format(len(mismatches)))
R.append('')

R.append('Mismatched functions:')
for name, status, result in mismatches:
    if status == 'MISSING in recompiled':
        R.append('  - {}: {}'.format(name, status))
    else:
        td = len(result['true_diffs'])
        jd = len(result['jump_diffs'])
        R.append('  - {}: true_diffs={}, jump_diffs={}'.format(name, td, jd))
R.append('')
R.append('Match rate: {}/{} = {:.1f}%'.format(matched, total, 100.0 * matched / total))
R.append('')

R.append('=' * 80)
R.append('SECTION 2: Detailed Bytecode Diff')
R.append('=' * 80)

for name, status, result in mismatches:
    if status == 'MISSING in recompiled':
        R.append('')
        R.append('--- {}: MISSING in recompiled ---'.format(name))
        R.append('This function exists in original but not in recompiled.')
        continue

    R.append('')
    R.append('--- {} ---'.format(name))
    R.append('  orig_instr_count: {}'.format(result['orig_count']))
    R.append('  decomp_instr_count: {}'.format(result['decomp_count']))
    R.append('  true_diffs: {}'.format(len(result['true_diffs'])))
    R.append('  jump_diffs: {}'.format(len(result['jump_diffs'])))

    orig_instrs = get_bytecode_instructions(orig_dict[name])
    orig_filtered = _filter_noise_instrs(orig_instrs)
    R.append('')
    R.append('  Original bytecode (filtered, {} instrs):'.format(len(orig_filtered)))
    for i in orig_filtered:
        R.append('    {}'.format(format_instr(i)))

    recomp_instrs = get_bytecode_instructions(recomp_dict[name])
    recomp_filtered = _filter_noise_instrs(recomp_instrs)
    R.append('')
    R.append('  Recompiled bytecode (filtered, {} instrs):'.format(len(recomp_filtered)))
    for i in recomp_filtered:
        R.append('    {}'.format(format_instr(i)))

    R.append('')
    R.append('  True diffs:')
    for d in result['true_diffs']:
        d_type = d.get('type', '')
        if d_type == 'extra_in_decomp':
            R.append('    idx={}: EXTRA in decomp: {}({})'.format(d['index'], d['decomp_op'], d['decomp_arg']))
        elif d_type == 'missing_in_decomp':
            R.append('    idx={}: MISSING in decomp: orig had {}({})'.format(d['index'], d['orig_op'], d['orig_arg']))
        else:
            R.append('    idx={}: orig={}({}) vs decomp={}({})'.format(
                d['index'], d.get('orig_op', '?'), d.get('orig_arg', '?'),
                d.get('decomp_op', '?'), d.get('decomp_arg', '?')))

R.append('')
R.append('=' * 80)
R.append('SECTION 3: Raw Bytecode (Unfiltered) for Mismatched Functions')
R.append('=' * 80)

for name, status, result in mismatches:
    if status != 'MISMATCH':
        continue
    R.append('')
    R.append('--- {} ---'.format(name))

    orig_instrs = get_bytecode_instructions(orig_dict[name])
    R.append('Original (raw, {} instrs):'.format(len(orig_instrs)))
    for i in orig_instrs:
        R.append('  {}'.format(format_instr(i)))

    recomp_instrs = get_bytecode_instructions(recomp_dict[name])
    R.append('Recompiled (raw, {} instrs):'.format(len(recomp_instrs)))
    for i in recomp_instrs:
        R.append('  {}'.format(format_instr(i)))

    R.append('')
    R.append('Code object comparison:')
    orig_c = orig_dict[name]
    recomp_c = recomp_dict[name]
    R.append('  orig  co_cellvars: {}'.format(orig_c.co_cellvars))
    R.append('  recomp co_cellvars: {}'.format(recomp_c.co_cellvars))
    R.append('  orig  co_freevars: {}'.format(orig_c.co_freevars))
    R.append('  recomp co_freevars: {}'.format(recomp_c.co_freevars))
    R.append('  orig  co_varnames: {}'.format(orig_c.co_varnames))
    R.append('  recomp co_varnames: {}'.format(recomp_c.co_varnames))
    R.append('  orig  co_names: {}'.format(orig_c.co_names))
    R.append('  recomp co_names: {}'.format(recomp_c.co_names))
    R.append('  orig  co_consts (non-code): {}'.format(
        [c for c in orig_c.co_consts if not isinstance(c, types.CodeType)]))
    R.append('  recomp co_consts (non-code): {}'.format(
        [c for c in recomp_c.co_consts if not isinstance(c, types.CodeType)]))

R.append('')
R.append('=' * 80)
R.append('SECTION 4: Root Cause Analysis')
R.append('=' * 80)
R.append('')
R.append('Mismatch function: system_func_with_execution_phase')
R.append('')
R.append('Original source (inferred from bytecode):')
R.append('  def system_func_with_execution_phase(execution_phase, func):')
R.append('      from IQEngine.core import execution_context as exc_ctxt')
R.append('      from IQEngine.const import ExcType')
R.append('      def wrapper(*args, **kwargs):')
R.append('          with exc_ctxt.ExecutionContext(execution_phase):')
R.append('              with ModifyExceptionFromType(ExcType.SYSTEM_EXC):')
R.append('                  return func(*(args), **(kwargs))')
R.append('      return wrapper')
R.append('')
R.append('Decompiled output (INCORRECT):')
R.append('  def system_func_with_execution_phase(execution_phase, func):')
R.append('      import IQEngine.core.execution_context')
R.append('      def wrapper(*args, **kwargs):')
R.append('          with exc_ctxt.ExecutionContext(execution_phase):')
R.append('              with ModifyExceptionFromType(ExcType.SYSTEM_EXC):')
R.append('                  return func(*(args), **(kwargs))')
R.append('      return wrapper')
R.append('')
R.append('Root cause: The decompiler (pycdc) incorrectly decompiled two import')
R.append('statements that use "from X import Y" syntax and store the imported')
R.append('names as closure variables (STORE_DEREF instead of STORE_FAST):')
R.append('')
R.append('1. "from IQEngine.core import execution_context as exc_ctxt" was')
R.append('   decompiled as "import IQEngine.core.execution_context". The')
R.append('   original bytecode uses IMPORT_FROM+SWAP+POP_TOP+IMPORT_FROM+')
R.append('   STORE_DEREF to extract "execution_context" and store it as')
R.append('   "exc_ctxt" (a cell variable for the nested wrapper function).')
R.append('   The decompiler lost the IMPORT_FROM and STORE_DEREF, instead')
R.append('   generating a bare "import X.Y" which stores only the top-level')
R.append('   package name as a local variable (STORE_FAST IQEngine).')
R.append('')
R.append('2. "from IQEngine.const import ExcType" was completely lost in the')
R.append('   decompiled output. The original bytecode has LOAD_CONST+')
R.append('   IMPORT_NAME+IMPORT_FROM+STORE_DEREF+POP_TOP for this import,')
R.append('   but none of these instructions appear in the recompiled code.')
R.append('')
R.append('3. Because the two import-from statements were not properly')
R.append('   decompiled, the closure variables (exc_ctxt, ExcType) that')
R.append('   should be captured by the nested wrapper function are missing')
R.append('   from the outer function. This causes the MAKE_FUNCTION closure')
R.append('   tuple to be wrong: original has 4 closures (ExcType, exc_ctxt,')
R.append('   execution_phase, func) but recompiled has only 2 (execution_phase,')
R.append('   func). The wrapper function itself then references undefined')
R.append('   names (exc_ctxt, ExcType) at runtime.')
R.append('')
R.append('This is a known pycdc limitation: it fails to properly decompile')
R.append('"from X import Y" statements when the imported name is stored as')
R.append('a cell/free variable (STORE_DEREF) rather than a local variable')
R.append('(STORE_FAST/STORE_NAME). This typically occurs when the imported')
R.append('name is referenced by a nested function (closure).')
R.append('')

R.append('=' * 80)
R.append('SECTION 5: Minimal Reproduction Examples')
R.append('=' * 80)
R.append('')
R.append('Each example is a minimal .py source code that, when compiled to .pyc')
R.append('with CPython 3.11, then decompiled with pycdc and recompiled, will')
R.append('produce a bytecode difference of the same category as the mismatch.')
R.append('')

# Generate 10+ minimal reproduction examples
# The core pattern is: from X import Y where Y becomes a closure variable

minimal_repros = [
    {
        'id': 1,
        'title': 'from-import with closure variable (simple)',
        'description': 'Import a name with "from X import Y" and use it in a nested function. '
                      'pycdc may decompile as "import X.Y" or lose the import entirely, '
                      'causing STORE_DEREF to become STORE_FAST or be omitted.',
        'code': '''\
import os

def outer():
    from os.path import join
    def inner(x):
        return join("a", x)
    return inner
''',
    },
    {
        'id': 2,
        'title': 'from-import as alias with closure variable',
        'description': 'Import with alias "from X import Y as Z" where Z is a closure '
                      'variable. pycdc may lose the alias, generating bare import or '
                      'wrong variable name.',
        'code': '''\
import os

def outer():
    from os.path import join as pjoin
    def inner(x):
        return pjoin("a", x)
    return inner
''',
    },
    {
        'id': 3,
        'title': 'Multiple from-imports with closure variables',
        'description': 'Multiple "from X import Y" statements where all imported names '
                      'are closure variables. pycdc may lose some or all imports.',
        'code': '''\
import os

def outer():
    from os.path import join
    from os.path import exists
    def inner(x):
        if exists(x):
            return join("a", x)
    return inner
''',
    },
    {
        'id': 4,
        'title': 'from-import with nested function using imported name in with-statement',
        'description': 'The imported name is used as a context manager in the nested '
                      'function. This matches the actual pattern in the mismatched code.',
        'code': '''\
import contextlib

def outer(phase):
    from contextlib import suppress as ctx
    def inner():
        with ctx(ValueError):
            return 42
    return inner
''',
    },
    {
        'id': 5,
        'title': 'from X.Y import Z with closure variable',
        'description': 'Multi-level package import "from X.Y import Z" where Z becomes '
                      'a closure variable. This is the exact pattern in the mismatched code '
                      '(from IQEngine.core import execution_context).',
        'code': '''\
import os

def outer():
    from os.path import basename
    def inner(x):
        return basename(x)
    return inner
''',
    },
    {
        'id': 6,
        'title': 'from-import closure with two nested functions',
        'description': 'Imported name is referenced by two different nested functions, '
                      'making it a cell variable with multiple consumers.',
        'code': '''\
import os

def outer():
    from os.path import join
    def inner1(x):
        return join("a", x)
    def inner2(x):
        return join("b", x)
    return inner1, inner2
''',
    },
    {
        'id': 7,
        'title': 'from-import with class attribute reference in closure',
        'description': 'Import an enum/class and access its attribute in the nested '
                      'function. Matches the ExcType.SYSTEM_EXC pattern.',
        'code': '''\
from enum import Enum

class MyEnum(Enum):
    A = 1
    B = 2

def outer(func):
    from enum import Enum as E
    def inner(*args):
        if E.A:
            return func(*args)
    return inner
''',
    },
    {
        'id': 8,
        'title': 'from-import closure + parameter closure combined',
        'description': 'Both the imported name and the outer function parameter are '
                      'closure variables. This matches the actual pattern where both '
                      'exc_ctxt and execution_phase are closures.',
        'code': '''\
import os

def outer(phase):
    from os.path import join
    def inner(x):
        return join(phase, x)
    return inner
''',
    },
    {
        'id': 9,
        'title': 'from-import with star-style module path and closure',
        'description': 'A deeply nested module path "from A.B.C import D" where D '
                      'becomes a closure variable.',
        'code': '''\
import collections

def outer():
    from collections.abc import Mapping
    def inner(x):
        return isinstance(x, Mapping)
    return inner
''',
    },
    {
        'id': 10,
        'title': 'from-import where name is used both locally and in closure',
        'description': 'The imported name is used both in the outer function body and '
                      'in the nested function, making it both a local and a cell variable.',
        'code': '''\
import os

def outer():
    from os.path import exists
    _ = exists(".")
    def inner(x):
        return exists(x)
    return inner
''',
    },
    {
        'id': 11,
        'title': 'from-import with decorator-like pattern (matches actual code)',
        'description': 'Closest pattern to the actual mismatched code: a decorator-like '
                      'function that imports modules and creates a closure over both '
                      'imported names and function parameters.',
        'code': '''\
def system_func_with_execution_phase(execution_phase, func):
    from contextlib import suppress as exc_ctxt
    from enum import Enum as ExcType
    def wrapper(*args, **kwargs):
        with exc_ctxt(ValueError):
            return func(*args, **kwargs)
    return wrapper
''',
    },
    {
        'id': 12,
        'title': 'from-import inside function vs module-level (control)',
        'description': 'Control case: the same import pattern at module level does NOT '
                      'produce STORE_DEREF (uses STORE_NAME instead). The difference '
                      'only manifests when the import is inside a function with a closure.',
        'code': '''\
from os.path import join

def inner(x):
    return join("a", x)
''',
    },
]

for ex in minimal_repros:
    R.append('Minimal Reproduction #{}: {}'.format(ex['id'], ex['title']))
    R.append('  Description: {}'.format(ex['description']))
    R.append('  Python source code:')
    for line in ex['code'].strip().split('\n'):
        R.append('    {}'.format(line))
    R.append('')

# Section 6: Verify minimal repros actually produce diffs
R.append('=' * 80)
R.append('SECTION 6: Verification of Minimal Reproduction Examples')
R.append('=' * 80)
R.append('')
R.append('For each minimal reproduction example, compile to .pyc, decompile,')
R.append('recompile, and compare bytecodes to verify the difference is real.')
R.append('')

import tempfile
import py_compile

verified_count = 0
verified_results = []

for ex in minimal_repros:
    code_text = ex['code'].strip()
    
    # Write to temp .py file
    tmp_py = os.path.join('d:\\Temp\\opencode', 'round81_repro_{}.py'.format(ex['id']))
    tmp_pyc = tmp_py + 'c'
    
    with open(tmp_py, 'w', encoding='utf-8') as f:
        f.write(code_text)
    
    # Compile to .pyc
    try:
        py_compile.compile(tmp_py, tmp_pyc, doraise=True)
    except Exception as e:
        R.append('Repro #{}: COMPILE FAIL: {}'.format(ex['id'], e))
        # Clean up
        for p in [tmp_py, tmp_pyc]:
            if os.path.exists(p):
                os.remove(p)
        continue
    
    # Decompile
    try:
        decomp_src = decompile_pyc(tmp_pyc)
    except Exception as e:
        R.append('Repro #{}: DECOMPILE FAIL: {}'.format(ex['id'], e))
        for p in [tmp_py, tmp_pyc]:
            if os.path.exists(p):
                os.remove(p)
        continue
    
    # Compile decompiled source
    try:
        orig_c = compile(code_text, '<original>', 'exec')
        recomp_c = compile(decomp_src, '<decompiled>', 'exec')
    except SyntaxError as e:
        R.append('Repro #{}: RECOMPILE FAIL: {}'.format(ex['id'], e))
        R.append('  Decompiled source:')
        for line in decomp_src.split('\n')[:20]:
            R.append('    {}'.format(line))
        for p in [tmp_py, tmp_pyc]:
            if os.path.exists(p):
                os.remove(p)
        continue
    
    # Extract code objects and compare
    orig_funcs_list = extract_code_objects(orig_c)
    recomp_funcs_list = extract_code_objects(recomp_c)
    
    orig_d = {name: code for name, code in orig_funcs_list}
    recomp_d = {name: code for name, code in recomp_funcs_list}
    
    has_mismatch = False
    mismatch_names = []
    for fname in orig_d:
        if fname not in recomp_d:
            has_mismatch = True
            mismatch_names.append('{}:MISSING'.format(fname))
            continue
        res = compare_bytecode(orig_d[fname], recomp_d[fname])
        if not res['match']:
            has_mismatch = True
            mismatch_names.append('{}:true_diffs={}'.format(fname, len(res['true_diffs'])))
    
    if has_mismatch:
        verified_count += 1
        R.append('Repro #{}: MISMATCH CONFIRMED - {}'.format(ex['id'], ', '.join(mismatch_names)))
        R.append('  Decompiled source:')
        for line in decomp_src.split('\n'):
            R.append('    {}'.format(line))
    else:
        R.append('Repro #{}: MATCH (no difference detected)'.format(ex['id']))
        R.append('  Decompiled source:')
        for line in decomp_src.split('\n'):
            R.append('    {}'.format(line))
    
    verified_results.append({
        'id': ex['id'],
        'title': ex['title'],
        'has_mismatch': has_mismatch,
        'mismatch_names': mismatch_names,
    })
    
    # Clean up
    for p in [tmp_py, tmp_pyc]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass

R.append('')
R.append('Verification summary: {}/{} examples confirmed as producing bytecode differences'.format(
    verified_count, len(minimal_repros)))
R.append('')

# Section 7: Full decompiled source
R.append('=' * 80)
R.append('SECTION 7: Full Decompiled Source')
R.append('=' * 80)
R.append('')
R.append(decompiled_source)

# Write the report
report_text = '\n'.join(R)
with open('F:/Downloads/pythoncdc-main/round81_test_report.txt', 'w', encoding='utf-8') as f:
    f.write(report_text)

print('Report written successfully.')
print('Total functions: {}'.format(total))
print('Matched: {}'.format(matched))
print('Mismatched: {}'.format(len(mismatches)))
print('Verified minimal repros with mismatches: {}/{}'.format(verified_count, len(minimal_repros)))
