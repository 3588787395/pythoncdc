"""R17 最小复现：data.sort(...) + return data 错误合并为 return data.sort(...)"""
import sys
import dis
import marshal
import importlib.util

sys.path.insert(0, '/workspace')

from pycdc import decompile_pyc

# 最小复现代码
SRC = '''
def load_get_index_stocks(stocks, date=None):
    data = []
    if isinstance(stocks, str):
        data = data_proxy().get_index_stocks_local(stocks, date)
    elif isinstance(stocks, list):
        stockslist = []
        for stock in stocks:
            stockslist.extend(data_proxy().get_index_stocks_local(stock, date))
        data = list(set(stockslist))
        data.sort(key=stockslist.index)
        return data
    return data
'''

# 编译为字节码
co = compile(SRC, '<test>', 'exec')
fn_code = None
for c in co.co_consts:
    if isinstance(c, type(compile('', '', 'exec'))) and c.co_name == 'load_get_index_stocks':
        fn_code = c
        break

print("=== 原始字节码 ===")
dis.dis(fn_code)
print()

# 用 pycdc 反编译这个最小代码
# 先写一个 pyc 文件
import struct
import time
import importlib.util

PYC = '/tmp/test_pop_top_return.pyc'
with open(PYC, 'wb') as f:
    # Python 3.11 pyc header: magic(4) + bit_field(4) + mtime(4) + size(4)
    magic_bytes = importlib.util.MAGIC_NUMBER  # 4 bytes
    f.write(magic_bytes)
    f.write(struct.pack('<I', 0))  # bit_field
    f.write(struct.pack('<I', int(time.time())))  # mtime
    f.write(struct.pack('<I', len(SRC.encode())))  # size
    f.write(marshal.dumps(co))

# 反编译
try:
    src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
    print("=== 反编译结果 ===")
    print(src)
    print()

    # 重新编译反编译结果
    new_co = compile(src, '<decompiled>', 'exec')
    new_fn_code = None
    for c in new_co.co_consts:
        if isinstance(c, type(compile('', '', 'exec'))) and c.co_name == 'load_get_index_stocks':
            new_fn_code = c
            break

    print("=== 反编译后的字节码 ===")
    dis.dis(new_fn_code)
    print()

    # 对比
    orig_instrs = [(i.opname, i.argval) for i in dis.get_instructions(fn_code) if i.opname not in ('CACHE', 'EXTENDED_ARG')]
    new_instrs = [(i.opname, i.argval) for i in dis.get_instructions(new_fn_code) if i.opname not in ('CACHE', 'EXTENDED_ARG')]

    print(f"=== 对比结果 ===")
    print(f"原始: {len(orig_instrs)} 指令")
    print(f"反编译: {len(new_instrs)} 指令")
    if orig_instrs == new_instrs:
        print("✓ 字节码完全一致！")
    else:
        print("✗ 字节码不一致")
        for i, (a, b) in enumerate(zip(orig_instrs, new_instrs)):
            if a != b:
                print(f"  差异位置 {i}: 原始={a}, 反编译={b}")
                # 显示上下文
                print(f"  原始上下文: {orig_instrs[max(0,i-2):i+3]}")
                print(f"  反编译上下文: {new_instrs[max(0,i-2):i+3]}")
                break
        if len(orig_instrs) != len(new_instrs):
            print(f"  长度差异: 原始={len(orig_instrs)}, 反编译={len(new_instrs)}")
except Exception as e:
    import traceback
    traceback.print_exc()
