import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
with open(pyc, 'rb') as f:
    f.read(16); code = marshal.load(f)

def extract_with_class(co, path=''):
    name = co.co_name or '<module>'
    result = []
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            result.extend(extract_with_class(c, path + '/' + name))
    result.append((path + '/' + name, co))
    return result

for path, co in extract_with_class(code):
    if co.co_name == 'post':
        print('=== %s ===' % path)
        print('co_varnames:', co.co_varnames[:10])
        print('Total instructions:', len(list(dis.get_instructions(co))))
