"""R21 diag: print CFG block layout of the second `_target` (py3.11 path) in handlers.pyc."""
import marshal
import sys
import types

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

from core.cfg import build_cfg  # noqa: E402


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out


def main():
    root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
    targets = [c for c in collect(root, []) if c.co_name == '_target']
    print(f'found {len(targets)} _target code objects')
    t = targets[0]  # the py3.11 defect path
    print(f'co_names: {t.co_names}')
    cfg = build_cfg(t)
    blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    print(f'--- blocks ({len(blocks)}) ---')
    for b in sorted(blocks, key=lambda x: x.start_offset):
        ops = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
        succs = sorted(s.start_offset for s in b.successors)
        print(f'block@{b.start_offset:4d} end={b.end_offset:4d} succs={succs} '
              f'entries={len(b.instructions)}: {ops}')


if __name__ == '__main__':
    main()
