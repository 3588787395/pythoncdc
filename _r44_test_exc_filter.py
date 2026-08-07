import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs, _classify_instruction
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQCommon/api/klinedata.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

source = decompile_pyc(pyc_path)
decomp_code = compile(source, '<decompiled>', 'exec')

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

# Test with additional exception handling noise filtering
EXC_NOISE = {'PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'POP_EXCEPT', 'RERAISE', 'COPY'}
ALL_NOISE = {'NOP', 'PRECALL', 'EXTENDED_ARG', 'COPY_FREE_VARS', 'MAKE_CELL'} | EXC_NOISE

def filter_all(instrs):
    return [i for i in instrs if i.opname not in ALL_NOISE]

# Test multiple functions
for name in ['get_kline_by_count', 'get_kline_by_date_one', 'get_kline_by_date_new']:
    if name not in orig_map or name not in decomp_map:
        continue
    orig_i = filter_all(list(dis.get_instructions(orig_map[name])))
    decomp_i = filter_all(list(dis.get_instructions(decomp_map[name])))
    
    # Count true diffs
    td = 0
    jd = 0
    for i in range(min(len(orig_i), len(decomp_i))):
        o = orig_i[i]
        d = decomp_i[i]
        o_a = o.argval if o.argval is not None else o.arg
        d_a = d.argval if d.argval is not None else d.arg
        if isinstance(o_a, types.CodeType):
            o_a = f"<code {o_a.co_name}>"
        if isinstance(d_a, types.CodeType):
            d_a = f"<code {d_a.co_name}>"
        # LOAD_ATTR vs LOAD_METHOD equivalence
        _o = o.opname
        _d = d.opname
        if {'LOAD_ATTR': 'LOAD_METHOD', 'LOAD_METHOD': 'LOAD_ATTR'}.get(_o) == _d:
            _o = _d
        if _o != _d:
            if _classify_instruction(o.opname) == 'jump' or _classify_instruction(d.opname) == 'jump':
                jd += 1
            else:
                td += 1
        elif str(o_a) != str(d_a):
            if _classify_instruction(o.opname) == 'jump':
                jd += 1
            else:
                td += 1
    
    extra = max(0, len(decomp_i) - len(orig_i))
    missing = max(0, len(orig_i) - len(decomp_i))
    td += extra + missing
    print(f"{name}: orig={len(orig_i)}, decomp={len(decomp_i)}, true_diffs={td}, jump_diffs={jd}, match={'YES' if td==0 else 'NO'}")
