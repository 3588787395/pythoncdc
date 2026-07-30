"""R25: analyze <module> NOPs - print context (prev2/next2) + starts_line for each NOP in orig."""
import sys, types, dis
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


def main():
    co = load_orig()
    instrs = [ins for ins in dis.get_instructions(co) if ins.opname != 'CACHE']
    # index by offset
    print(f"=== ORIG <module>: total instr (skip CACHE) = {len(instrs)}, NOP count below ===")
    nop_count = sum(1 for ins in instrs if ins.opname == 'NOP')
    print(f"NOP count = {nop_count}")
    print(f"\n=== Each NOP with prev2 + next2 context + starts_line ===\n")
    # map offset -> index
    for i, ins in enumerate(instrs):
        if ins.opname != 'NOP':
            continue
        ctx_start = max(0, i - 2)
        ctx_end = min(len(instrs), i + 3)
        print(f"--- NOP @ offset {ins.offset}  starts_line={ins.starts_line} ---")
        for j in range(ctx_start, ctx_end):
            x = instrs[j]
            mark = '>>>' if j == i else '   '
            sl = x.starts_line or ''
            print(f"  {mark} {x.offset:>5} L{str(sl):>5}  {x.opname:<22} {x.argrepr}")
        print()

    # also: pattern summary - what instruction precedes each NOP cluster and follows
    print("=== NOP cluster boundaries (prev instr -> NOPs -> next instr) ===")
    clusters = []
    i = 0
    while i < len(instrs):
        if instrs[i].opname == 'NOP':
            start = i
            while i < len(instrs) and instrs[i].opname == 'NOP':
                i += 1
            end = i  # exclusive
            prev_ins = instrs[start - 1] if start > 0 else None
            next_ins = instrs[end] if end < len(instrs) else None
            clusters.append((start, end, prev_ins, next_ins, [instrs[k].starts_line for k in range(start, end)]))
        else:
            i += 1
    print(f"NOP clusters: {len(clusters)}, total NOPs: {sum(c[1]-c[0] for c in clusters)}")
    for idx, (s, e, p, n, sls) in enumerate(clusters):
        p_repr = f"{p.offset}@L{p.starts_line} {p.opname} {p.argrepr}" if p else 'None'
        n_repr = f"{n.offset}@L{n.starts_line} {n.opname} {n.argrepr}" if n else 'None'
        print(f"  cluster#{idx}: {e-s} NOPs offsets {instrs[s].offset}-{instrs[e-1].offset} starts_lines={sls}")
        print(f"     PREV: {p_repr}")
        print(f"     NEXT: {n_repr}")


if __name__ == '__main__':
    main()
