"""对比 use_cfg=True / False 两条流水线在同一 pyc 上的表现，确认缺陷归属。"""
import sys
import dis
import types
import marshal

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)
from pycdc import decompile_pyc

PYC = ROOT + r'\site-packages\IQEngine\account\order.pyc'


def find(co, name, out):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                out.append(c)
            find(c, name, out)


def norm(co):
    out = []
    for ins in dis.get_instructions(co):
        if 'JUMP' in ins.opname or ins.opname == 'FOR_ITER':
            out.append((ins.opname, '<J>'))
        else:
            out.append((ins.opname, ins.argval))
    return out


def main():
    with open(PYC, 'rb') as f:
        f.read(16)
        orig = marshal.load(f)
    o = []
    find(orig, 'save', o)
    oco = o[0]
    oins = list(dis.get_instructions(oco))
    print('原始 save(): %d 条指令, %d 个 MAP_ADD'
          % (len(oins), sum(1 for x in oins if x.opname == 'MAP_ADD')))

    for mode in (False, True):
        print()
        print('=== use_cfg=%s ===' % mode)
        try:
            src = decompile_pyc(PYC, use_cfg=mode)
        except Exception as e:
            print('  反编译异常:', type(e).__name__, str(e)[:100])
            continue
        i = src.find('def save(')
        snippet = src[i:i + 220] if i >= 0 else 'NOT FOUND'
        print('  产物:', snippet.replace('\n', ' ')[:200])
        try:
            re_mod = compile(src, '<decomp>', 'exec')
        except SyntaxError as e:
            print('  重编译 SyntaxError:', str(e)[:80])
            continue
        r = []
        find(re_mod, 'save', r)
        if not r:
            print('  重编译后无 save')
            continue
        rins = list(dis.get_instructions(r[0]))
        print('  重编译 save(): %d 条指令, %d 个 MAP_ADD'
              % (len(rins), sum(1 for x in rins if x.opname == 'MAP_ADD')))
        a, b = norm(oco), norm(r[0])
        if a == b:
            print('  结果: BYTE-IDENTICAL')
        else:
            n = 0
            for k in range(max(len(a), len(b))):
                x = a[k] if k < len(a) else None
                y = b[k] if k < len(b) else None
                if x != y:
                    print('  结果: DIFF  首个差异 @%d  A:%s  B:%s' % (k, x, y))
                    break


if __name__ == '__main__':
    main()
