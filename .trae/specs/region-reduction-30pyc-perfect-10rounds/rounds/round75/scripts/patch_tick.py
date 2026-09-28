# -*- coding: utf-8 -*-
"""一次性补丁：把 tick75.py 的 section-4（字节级内容）改用 matched Inst 对象的 offset/bytecode。"""
import io
import sys

P = r'D:\Temp\opencode\r75gate\diag1\tick75.py'
sys.stdout.reconfigure(encoding='utf-8')
t = io.open(P, encoding='utf-8').read()
a = t.index('        # ---- 4.')
b = t.index('        io.open(OUT,')
new = '''        # ---- 4. 字节级内容（matched Inst 的 offset / bytecode 切片） ----
        out.append('## 4. 字节级内容（matched 指令表：`idx` / `offset` / `co_code` 字节；'
                   '与 §2、§3 的 index 完全同一空间）')
        out.append('')

        def ibytes(insts, i1, i2):
            rows = []
            for k in range(i1, i2):
                x = insts[k]
                buf = x.bytecode
                try:
                    n = getattr(x, 'inst_size', 2) or 2
                    hx = bytes(buf[x.offset:x.offset + n]).hex()
                except Exception:
                    hx = ''
                ar = x.argrepr if x.arg is not None else ''
                rows.append('- %4d off=%-6d %-6s %-44s %s' % (k, x.offset, hx, x.opname, ar))
            return rows

        la = res.get('landed')
        if la:
            out.append('### orig（matched，len=%d）· 三个归一化 hunk 的 orig 侧' % len(la['ins_a']))
            for j, (tt, i1, i2, j1, j2) in enumerate(la['norm_opcodes'], 1):
                out.append('- hunk #%d `%s` orig[%d:%d]' % (j, tt, i1, i2))
                if i1 < i2:
                    out.extend(ibytes(la['ins_a'], i1, i2))
            out.append('')
        for tag, _ in srcs:
            r = res.get(tag)
            if not r:
                continue
            out.append('### arm=%s（matched，len=%d）· hunks_norm=%d' % (tag, len(r['ins_b']), r['hunks_norm']))
            for j, (tt, i1, i2, j1, j2) in enumerate(r['norm_opcodes'], 1):
                out.append('- hunk #%d `%s` -> prod[%d:%d]' % (j, tt, j1, j2))
                if j1 < j2:
                    out.extend(ibytes(r['ins_b'], j1, j2))
            out.append('')
'''
t = t[:a] + new + t[b:]
# seq_of 改为返回 Inst 列表；metrics 调用处做 tup() 转换
t = t.replace("""    if ia is None or ib is None:
        return None, None
    return [tup(x) for x in ia], [tup(x) for x in ib]""",
              """    return ia, ib""")
t = t.replace("""                res[tag] = metrics(ia, ib)""",
              """                res[tag] = metrics([tup(x) for x in ia], [tup(x) for x in ib])
                res[tag]['ins_a'], res[tag]['ins_b'] = ia, ib""")
t = t.replace("""                if ia is None or ib is None:""",
              """                if ia is None or ib is None:""")
io.open(P, 'w', encoding='utf-8', newline='\n').write(t)
print('patched', P, 'len', len(t))
