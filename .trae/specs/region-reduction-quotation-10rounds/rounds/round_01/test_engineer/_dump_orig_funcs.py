"""快速反汇编原始 quotation.pyc 中 9 个不一致函数的字节码结构。"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
TARGETS = [
    'fill_minute_or_day_blank',
    'one_prod_to_dataframe',
    'load_bars_from_hundsun',
    'get_str_data',
    'change_his_to_backward',
    'get_date_and_count',
    'load_get_price',
    'build_future_fill_time',
]

module = load_pyc_file_v2(PYC)
co = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(co, 'to_python_code'):
    co = co.to_python_code()

sink = {}
def walk(c, prefix=''):
    name = '<module>' if (c.co_name == '<module>' and not prefix) else prefix + c.co_name
    sink[name] = c
    sub = '' if name == '<module>' else name + '.'
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            walk(k, sub)
walk(co)

for fn in TARGETS:
    if fn not in sink:
        print(f"### {fn}: NOT FOUND")
        continue
    print(f"\n{'='*70}\n### {fn}  (sub-codes: {[k.co_name for k in sink[fn].co_consts if isinstance(k, types.CodeType)]})\n{'='*70}")
    for ins in dis.get_instructions(sink[fn]):
        if ins.opname in ('EXTENDED_ARG', 'CACHE', 'RESUME', 'NOP', 'PRECALL'):
            continue
        av = ins.argval
        if isinstance(av, types.CodeType):
            av = f'<code {av.co_name}>'
        elif isinstance(av, str) and len(av) > 40:
            av = av[:40] + '...'
        print(f"  {ins.offset:5d} {ins.opname:26s} {av!r}")
