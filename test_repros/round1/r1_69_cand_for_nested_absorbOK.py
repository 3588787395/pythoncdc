# Source Generated with Decompyle++ (Python version)
# File: r1_69_cand_for_nested_absorb.pyc (Python 3.11)

def f69(xs, start, end):
    for n in xs:
        if len(n) == 1:
            if n[0] == start:
                continue
            elif n[0] == end:
                pre = n[0]
                if pre is not None:
                    tmp = n[1:]
                    if not tmp:
                        print('empty')
                        continue
                    print('full')
                    continue
        print('none')
    print('after-loop')
