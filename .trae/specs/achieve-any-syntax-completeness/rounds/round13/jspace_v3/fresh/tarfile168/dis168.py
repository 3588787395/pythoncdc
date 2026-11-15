#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble one function from a pyc (real) and from a product .py (recompiled),
printing raw instruction stream with offset-numbered jump targets.

usage: python -I -X utf8 dis168.py <pyc-or-py> <py|pyc> <funcname> [outfile]
"""
import dis
import marshal
import sys
import types


def load_root(path):
    if path.endswith('.pyc'):
        with open(path, 'rb') as f:
            f.read(16)
            return marshal.load(f)
    with open(path, 'rb') as f:
        src = f.read()
    return compile(src, path, 'exec')


def find_codes(root):
    out = []

    def walk(code, prefix):
        out.append((prefix + code.co_name, code))
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                walk(c, prefix + code.co_name + '.')
    walk(root, '')
    return out


def dump(code, title, lines):
    instrs = list(dis.get_instructions(code))
    lines.append('==== %s  (n_instrs=%d)' % (title, len(instrs)))
    idx_by_off = {ins.offset: k for k, ins in enumerate(instrs)}
    for k, ins in enumerate(instrs):
        tgt = ''
        if ins.is_jump_target:
            tgt += ' [T]'
        if ins.opcode in dis.hasjrel or ins.opcode in dis.hasjabs:
            a = ins.argval
            tgt += ' ->#%s(@%s)' % (idx_by_off.get(a, '?'), a)
        arg = '' if ins.arg is None else ' %r' % (ins.argval,)
        lines.append('  #%-3d @%-5d %-32s%s%s' % (k, ins.offset, ins.opname, arg, tgt))


def main():
    real, prod, name = sys.argv[1], sys.argv[2], sys.argv[3]
    out = sys.argv[4] if len(sys.argv) > 4 else None
    r = dict(find_codes(load_root(real)))
    p = dict(find_codes(load_root(prod)))
    lines = []
    code = r.get(name)
    if code is None:
        cands = [k for k in r if k.endswith(name)]
        lines.append('not found; candidates: %s' % (cands[:20],))
    else:
        dump(code, 'REAL ' + name, lines)
    pc = p.get(name)
    if pc is None:
        cands = [k for k in p if k.endswith(name)]
        lines.append('prod not found; candidates: %s' % (cands[:20],))
    else:
        dump(pc, 'PROD ' + name, lines)
    text = '\n'.join(lines)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text + '\n')
        print('wrote', out, len(lines), 'lines')
    else:
        print(text)


if __name__ == '__main__':
    main()
