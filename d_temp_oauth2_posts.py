import sys, types, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(co, name, parent_name=None, path=''):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                if parent_name is None or co.co_name == parent_name:
                    return c
            r = find_code(c, name, parent_name, path + '/' + co.co_name)
            if r: return r
    return None

# Show all post functions with their class context
def show_all_posts(co, path=''):
    name = co.co_name or '<module>'
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            show_all_posts(c, path + '/' + name)
    if co.co_name == 'post':
        print(f"post function: path={path}/{name} varnames={co.co_varnames[:5]}")

with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
show_all_posts(code)
