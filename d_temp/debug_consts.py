import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

with open(r'F:\Downloads\pythoncdc-main\site-packages\IQData\utils\common_func.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

print("Top-level co_consts types:")
for i, c in enumerate(code.co_consts):
    if isinstance(c, types.CodeType):
        print("  [{}]: CodeType name={}".format(i, c.co_name))
    else:
        print("  [{}]: {} type={}".format(i, repr(c)[:50], type(c).__name__))
