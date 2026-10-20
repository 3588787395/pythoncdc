import dis, marshal, importlib.util, sys, io, os

ROOT = r'F:\Downloads\pythoncdc-main'
PYC = os.path.join(ROOT, r'test_repros\round2\x01_if_deep_hosts.pyc')
OK = os.path.join(ROOT, r'.trae\specs\attain-true-completeness\test_repros\round5\rec1_x01_x01_if_deep_hostsOK.py')

def load_pyc_codes(path):
    with open(path, 'rb') as f:
        data = f.read()
    code = marshal.loads(data[16:])
    return code

def find_code(code, name):
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            r = find_code(c, name)
            if r is not None:
                return r
    return None

def dis_str(code):
    buf = io.StringIO()
    dis.dis(code, file=buf)
    return buf.getvalue()

orig = load_pyc_codes(PYC)
tgt = find_code(orig, 'if_in_match')
print('=== ORIGINAL pyc if_in_match ===')
print(dis_str(tgt))

with open(OK, 'rb') as f:
    src = f.read().decode('utf-8')
# extract the if_in_match function source
import ast as _ast
tree = _ast.parse(src)
fn = None
for node in tree.body:
    if isinstance(node, _ast.FunctionDef) and node.name == 'if_in_match':
        fn = node
        break
if fn is None:
    print('!! if_in_match not found in OK.py')
else:
    seg = _ast.get_source_segment(src, fn)
    print('=== OK.py if_in_match source ===')
    print(seg)
    comp = compile(seg, '<ok>', 'exec')
    c2 = find_code(comp, 'if_in_match')
    print('=== RECOMPILED OK if_in_match ===')
    print(dis_str(c2))
