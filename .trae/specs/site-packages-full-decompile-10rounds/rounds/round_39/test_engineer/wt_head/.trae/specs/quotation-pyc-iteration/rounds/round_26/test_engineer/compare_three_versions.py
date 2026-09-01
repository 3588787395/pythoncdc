"""R26: 精确对比get_option_info的两种等价源码结构
版本A: if not + 显式continue (after_if是continue)
版本B: 两个独立if (if cond: continue)
"""
import dis
import types

# 版本A: if not + 显式continue
srcA = '''
def fA(items, dict1, data_out):
    for i in items:
        for key, value in i.items():
            if not key == 'price_change_ratio':
                if key == 'trading_time_desc':
                    continue
                elif isinstance(value, dict):
                    dict1.update(value)
                    continue
                else:
                    dict1[key] = value
                    continue
            continue
        data_out.append(dict1)
'''

# 版本B: 两个独立if
srcB = '''
def fB(items, dict1, data_out):
    for i in items:
        for key, value in i.items():
            if key == 'price_change_ratio':
                continue
            if key == 'trading_time_desc':
                continue
            elif isinstance(value, dict):
                dict1.update(value)
                continue
            else:
                dict1[key] = value
                continue
        data_out.append(dict1)
'''

# 版本C: if not 无显式continue (反编译器生成的结构)
srcC = '''
def fC(items, dict1, data_out):
    for i in items:
        for key, value in i.items():
            if not key == 'price_change_ratio':
                if key == 'trading_time_desc':
                    continue
                elif isinstance(value, dict):
                    dict1.update(value)
                    continue
                else:
                    dict1[key] = value
                    continue
        data_out.append(dict1)
'''

def get_instrs(co):
    out = []
    for ins in dis.get_instructions(co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        out.append((ins.offset, ins.opname, ins.argval, ins.argrepr))
    return out

def find_co(co, name):
    for c in co.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == name:
            return c
    return None

for label, src in [('A (if not + continue)', srcA), ('B (two ifs)', srcB), ('C (if not no continue)', srcC)]:
    co = compile(src, label, 'exec')
    f = find_co(co, 'f' + label[0])
    instrs = get_instrs(f)
    print(f"\n=== 版本{label} ({len(instrs)} instrs) ===")
    # 只显示内层for循环体部分 (620附近)
    for ins in instrs:
        if 60 <= ins[0] <= 190:
            print(f"  {ins[0]:>4} {ins[1]:<35} {ins[3]}")

# 对比A和B是否一致
iA = [(i[1], i[2]) for i in get_instrs(find_co(compile(srcA,'A','exec'), 'fA'))]
iB = [(i[1], i[2]) for i in get_instrs(find_co(compile(srcB,'B','exec'), 'fB'))]
iC = [(i[1], i[2]) for i in get_instrs(find_co(compile(srcC,'C','exec'), 'fC'))]
print(f"\nA == B: {iA == iB}")
print(f"A == C: {iA == iC}")
print(f"B == C: {iB == iC}")
