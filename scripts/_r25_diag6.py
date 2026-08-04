"""R25 diag6: Compare decompiled vs original"""
import sys
sys.path.insert(0, '.')
from core.cfg import decompile

src = '''
def test():
    try:
        x = 1
    except BaseException:
        while x != 0:
            try:
                x = x - 1
            except BaseException:
                x = 0
        else:
            if x == 0:
                return None
    else:
        if x > 0:
            try:
                return x
            except BaseException:
                return None
        else:
            return -1
'''

result = decompile(src, '<test>')
print("=== Decompiled ===")
print(result)

# Compile original and decompiled, compare bytecodes
orig_code = compile(src, '<orig>', 'exec')
decomp_code = compile(result, '<decompiled>', 'exec')

for orig_c, decomp_c in zip(orig_code.co_consts, decomp_code.co_consts):
    if hasattr(orig_c, 'co_code') and hasattr(decomp_c, 'co_code'):
        orig_bytes = list(orig_c.co_code)
        decomp_bytes = list(decomp_c.co_code)
        if orig_bytes == decomp_bytes:
            print(f"\nBytecode MATCH for {orig_c.co_name} ({len(orig_bytes)} bytes)")
        else:
            print(f"\nBytecode MISMATCH for {orig_c.co_name}")
            print(f"  Original: {len(orig_bytes)} bytes")
            print(f"  Decompiled: {len(decomp_bytes)} bytes")
            # Find first difference
            for i in range(min(len(orig_bytes), len(decomp_bytes))):
                if orig_bytes[i] != decomp_bytes[i]:
                    print(f"  First diff at byte {i}: orig={orig_bytes[i]}, decomp={decomp_bytes[i]}")
                    break
