#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R3 字节码取证：dump 指定 .pyc 的函数级反汇编（含异常表）。
用法: python _r3_dis.py <pyc> [qualname-substr ...]
不传 qualname 则 dump 全部函数。
"""
import dis
import marshal
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def walk(code, prefix='<module>'):
    yield prefix, code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            name = c.co_qualname if hasattr(c, 'co_qualname') else c.co_name
            yield from walk(c, name)


def main():
    pyc = sys.argv[1]
    subs = sys.argv[2:]
    top = load_code(pyc)
    for qual, code in walk(top):
        if subs and not any(s in qual for s in subs):
            continue
        print('=' * 90)
        print('QUALNAME:', qual, '| firstlineno:', code.co_firstlineno, '| argcount:', code.co_argcount)
        print('varnames:', code.co_varnames, '| names:', code.co_names, '| consts:', [repr(c)[:80] for c in code.co_consts])
        dis.dis(code, depth=0)
        print('--- exception table ---')
        et = getattr(code, 'co_exceptiontable', b'')
        if et:
            i = 0
            while i < len(et):
                b0 = et[i]
                entry = {'start': None, 'end': None, 'target': None, 'depth': None, 'lasti': None}
                def read_varint(data, pos):
                    val = data[pos] & 0x3F
                    cont = True
                    if not (data[pos] & 0x40):
                        return val, pos + 1
                    val = val << 6 | (data[pos] & 0x3F)
                    pos += 1
                    if not (data[pos] & 0x40):
                        return val, pos + 1
                    return (val << 6) | (data[pos] & 0x3F), pos + 1
                start, i = read_varint(et, i)
                length, i = read_varint(et, i)
                target, i = read_varint(et, i)
                depth_lasti = et[i]; i += 1
                depth = depth_lasti >> 4
                lasti = depth_lasti & 0xF
                print('  [%d, %d) -> %d depth=%d lasti=%s' % (start, start + length, target, depth, lasti))
        else:
            print('  (none)')


if __name__ == '__main__':
    main()
