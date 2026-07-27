"""反汇编 quotation.pyc 中指定函数的字节码"""
import sys, types, marshal, dis

PYC = '/workspace/quotation.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# 收集所有 code object
def collect(c, prefix=''):
    name = '<module>' if not prefix else prefix + '.' + c.co_name
    yield name, c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from collect(k, name)

all_codes = dict(collect(code))

# 打印指定函数的字节码
targets = sys.argv[1:] if len(sys.argv) > 1 else ['<module>.change_future_real_date', '<module>._is_same_type_date', '<module>.api_get']

for t in targets:
    if t not in all_codes:
        print(f"NOT FOUND: {t}")
        matches = [k for k in all_codes if t in k]
        if matches:
            print(f"  candidates: {matches[:5]}")
        continue
    print(f"\n=== {t} (nlocals={all_codes[t].co_nlocals}, varnames={all_codes[t].co_varnames}) ===")
    for ins in dis.get_instructions(all_codes[t]):
        print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
