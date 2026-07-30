"""R25: dump dis for specific functions from orig pyc and new compiled."""
import sys, types, dis, os
sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
DECOMPILED = '/tmp/r25_decompiled.py'


def load_orig():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    co = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(co, 'to_python_code'):
        co = co.to_python_code()
    return co


def walk_code(co, prefix='', sink=None):
    if sink is None:
        sink = {}
    name = '<module>' if (co.co_name == '<module>' and not prefix) else prefix + co.co_name
    sink[name] = co
    sub = '' if name == '<module>' else name + '.'
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            walk_code(const, sub, sink)
    return sink


def find_co(co_dict, name):
    for k, v in co_dict.items():
        if k == name or k.endswith('.' + name):
            return v
    return None


def dump(co, label, fout=None):
    print(f"\n{'='*70}\n{label}: {co.co_name}  co_firstlineno={co.co_firstlineno}\n{'='*70}", file=fout)
    for ins in dis.get_instructions(co):
        if ins.opname == 'CACHE':
            continue
        sl = ins.starts_line or ''
        print(f"{ins.offset:>5} {str(sl):>5}  {ins.opname:<22} {ins.argrepr}", file=fout)


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else ['build_future_fill_time']
    orig_co = load_orig()
    orig_cos = walk_code(orig_co)
    with open(DECOMPILED) as f:
        src = f.read()
    new_code = compile(src, '<d>', 'exec')
    new_cos = walk_code(new_code)
    for t in targets:
        oc = find_co(orig_cos, t)
        nc = find_co(new_cos, t)
        out_path = f"/tmp/r25_dis_{t}.txt"
        with open(out_path, 'w') as fout:
            if oc:
                dump(oc, 'ORIG', fout)
            else:
                print(f"ORIG {t} not found", file=fout)
            if nc:
                dump(nc, 'NEW', fout)
            else:
                print(f"NEW {t} not found", file=fout)
        print(f"wrote {out_path}")


if __name__ == '__main__':
    main()
