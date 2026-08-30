"""对比 _process_task_queue 原始与反编译字节码,输出所有差异段。"""
import sys, marshal, types, dis, io, py_compile, importlib.util
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')


def load_code(path, header=True):
    with open(path, 'rb') as f:
        if header:
            f.read(16)
        return marshal.load(f)


def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType) and c.co_name != '<lambda>':
            r = find_code(c, name)
            if r:
                return r
    return None


def extract(fn):
    """返回 (offset, opname, argval) 列表"""
    out = []
    for ins in dis.get_instructions(fn):
        out.append((ins.offset, ins.opname, ins.argval))
    return out


def main():
    orig = load_code(r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\graph.pyc')
    o_fn = find_code(orig, '_process_task_queue')

    ok_py = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\graphOK.py'
    cfile = py_compile.compile(ok_py, doraise=True, quiet=2)
    if cfile is None:
        cfile = importlib.util.cache_from_source(ok_py)
    decomp = load_code(cfile)
    d_fn = find_code(decomp, '_process_task_queue')

    ol = extract(o_fn)
    dl = extract(d_fn)
    print('orig=%d decomp=%d' % (len(ol), len(dl)))

    # 对齐比较:找连续差异段
    i = j = 0
    while i < len(ol) and j < len(dl):
        if ol[i][1] == dl[j][1] and (ol[i][0] == dl[j][0] or True):
            # opname 相同——跳过(无论 arg 是否一致,先看 opcode 序列)
            if ol[i][1] == dl[j][1]:
                i += 1
                j += 1
                continue
        # opname 不同:输出差异段
        seg_o = []
        seg_d = []
        while i < len(ol) and j < len(dl) and ol[i][1] != dl[j][1]:
            seg_o.append(ol[i])
            seg_d.append(dl[j])
            i += 1
            j += 1
        if seg_o:
            print('--- diff block ---')
            for k in range(max(len(seg_o), len(seg_d))):
                so = seg_o[k] if k < len(seg_o) else None
                sd = seg_d[k] if k < len(seg_d) else None
                if so and sd:
                    mark = '  ' if so[1] == sd[1] else '>>'
                    print('%s orig@%-4d %-28s %-12s | decomp@%-4d %-28s %-12s' % (
                        mark, so[0], so[1], str(so[2])[:10], sd[0], sd[1], str(sd[2])[:10]))
                elif so:
                    print('  orig@%-4d %-28s %-12s | (decomp end)' % (so[0], so[1], str(so[2])[:10]))
                else:
                    print('  (orig end)              | decomp@%-4d %-28s %-12s' % (sd[0], sd[1], str(sd[2])[:10]))
        # 对齐下一个匹配点(找下一个相同 opname)
        while i < len(ol) and j < len(dl) and ol[i][1] != dl[j][1]:
            i += 1
        if i >= len(ol) or j >= len(dl):
            break


if __name__ == '__main__':
    main()
