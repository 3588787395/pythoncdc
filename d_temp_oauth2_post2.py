import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
with open(pyc, 'rb') as f:
    f.read(16); code = marshal.load(f)

# Extract all code objects with class context
def extract_with_class(co, path=''):
    name = co.co_name or '<module>'
    result = {}
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            result.update(extract_with_class(c, path + '/' + name))
    key = path + '/' + name
    result[key] = co
    # Also store by just co_name (like the verify script)
    result[co.co_name or '<module>'] = co
    return result

orig = extract_with_class(code)

# Now compile the OK.py
import py_compile, importlib.util
ok_path = pyc.replace('.pyc', 'OK.py')
cf = py_compile.compile(ok_path, doraise=True, quiet=2)
if cf is None:
    cf = importlib.util.cache_from_source(ok_path)
with open(cf, 'rb') as f:
    f.read(16); decomp_code = marshal.load(f)

decomp = extract_with_class(decomp_code)

# Show the 'post' entries
print("=== ORIG 'post' entries ===")
for k, v in orig.items():
    if k == 'post' or k.endswith('/post'):
        print(f"  {k}: varnames={v.co_varnames[:5]}, instrs={len(list(dis.get_instructions(v)))}")

print("\n=== DECOMP 'post' entries ===")
for k, v in decomp.items():
    if k == 'post' or k.endswith('/post'):
        print(f"  {k}: varnames={v.co_varnames[:5]}, instrs={len(list(dis.get_instructions(v)))}")
