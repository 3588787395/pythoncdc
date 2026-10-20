"""[R5] x01 fix1 per-function bitwise comparison: old baseline OK vs new OK.

Purpose: confirm [B122-V3R5] changes ONLY if_in_match (green target) and
leaves every other unit (incl. domain-out if_in_while) bitwise unchanged.
"""
import re
import sys

OK_OLD = (r'.trae\specs\attain-true-completeness\test_repros\round5'
          r'\rec1_x01_x01_if_deep_hostsOK.py')
OK_NEW = (r'.trae\specs\attain-true-completeness\test_repros\round5'
          r'\rec1_x01_r5fix1_x01_if_deep_hostsOK.py')


def funcs(path):
    txt = open(path, encoding='utf-8').read()
    out = {}
    cur = None
    buf = []
    for line in txt.splitlines():
        m = re.match(r'(?:async )?def (\w+)\(', line)
        if m:
            if cur:
                out[cur] = '\n'.join(buf)
            cur = m.group(1)
            buf = [line]
        elif cur:
            if line and not line.startswith(' ') and not line.startswith(')'):
                out[cur] = '\n'.join(buf)
                cur = None
                buf = []
            else:
                buf.append(line)
    if cur:
        out[cur] = '\n'.join(buf)
    return out


def main():
    old = funcs(OK_OLD)
    new = funcs(OK_NEW)
    changed = []
    for k in sorted(old):
        same = old[k] == new.get(k)
        tag = 'IDENTICAL' if same else 'CHANGED'
        print(f'{k}: {tag}')
        if not same:
            changed.append(k)
    print('changed:', changed if changed else 'NONE')
    print('verdict:', 'PASS' if changed == ['if_in_match'] else 'CHECK')


if __name__ == '__main__':
    sys.exit(main())
