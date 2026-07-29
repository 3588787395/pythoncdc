"""R6 repro_01: 两条连续 strptime 语句，每条含 and/or 三元，第二条被吞。

缺陷：quotation.fill_minute_or_day_blank 中 source_start/source_end 两条
qdt.datetime.strptime(... + (... and ... or 'NNNN'), ...) 语句结构相同，
第一条 '0000' 正确反编译，第二条 '1530' 被吞 -> 残留 """1530""" 杂散字符串
+ 错误 if source_end[8:] or '1530': 条件。
"""
import dis, marshal, struct


def src():
    def f(a, b, g):
        if len(b) > 0:
            x = g(a[:8] + (len(a[8:]) == 4 and a[8:] or '0000'), '%Y%m%d%H%M')
            y = g(b[:8] + (len(b[8:]) == 4 and b[8:] or '1530'), '%Y%m%d%H%M')
            z = b[(~b < x) & (~b > y)]
            if len(z) > 0:
                return z
    return f


def main():
    co = compile(src.__code__.co_consts[0], '<repro>', 'exec')
    # write pyc
    with open('/tmp/repro_01.pyc', 'wb') as fh:
        fh.write(struct.pack('<H', 3495) + b'\r\n' + b'\x00'*10)
        marshal.dump(co, fh)
    print('=== orig dis ===')
    dis.dis(co)
    print()
    # decompile
    import sys
    sys.path.insert(0, '/workspace')
    from pycdc import decompile_pyc
    out = decompile_pyc('/tmp/repro_01.pyc', use_cfg=False, cfg_hybrid=False)
    print('=== decompiled ===')
    print(out)
    with open('/tmp/repro_01_out.py', 'w') as fh:
        fh.write(out)


if __name__ == '__main__':
    main()
