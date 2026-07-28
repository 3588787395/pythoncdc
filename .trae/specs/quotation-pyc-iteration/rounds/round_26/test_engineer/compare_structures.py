"""R26: 对比两种代码结构的字节码差异
原始结构（两个独立if + continue）vs 反编译结构（嵌套if）
"""
import dis
import types

# 版本1: 原始结构（两个独立if）
src1 = '''
def f1(items, dict1, data_out):
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

# 版本2: 反编译结构（嵌套if）
src2 = '''
def f2(items, dict1, data_out):
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

co1 = compile(src1, 'v1', 'exec')
co2 = compile(src2, 'v2', 'exec')

def find_co(co, name):
    for c in co.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == name:
            return c
    return None

f1 = find_co(co1, 'f1')
f2 = find_co(co2, 'f2')

print("=== 版本1 (两个独立if) 字节码 ===")
for ins in dis.get_instructions(f1):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")

print("\n=== 版本2 (嵌套if) 字节码 ===")
for ins in dis.get_instructions(f2):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")

# Compare lengths
i1 = [(i.offset, i.opname, i.argval) for i in dis.get_instructions(f1) if i.opname not in ('EXTENDED_ARG','CACHE')]
i2 = [(i.offset, i.opname, i.argval) for i in dis.get_instructions(f2) if i.opname not in ('EXTENDED_ARG','CACHE')]
print(f"\n版本1指令数: {len(i1)}, 版本2指令数: {len(i2)}")
print(f"字节码一致: {i1 == i2}")
