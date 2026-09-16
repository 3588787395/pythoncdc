import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
with open(pyc, 'rb') as f:
    f.read(16); code = marshal.load(f)

def extract_with_class(co, path=''):
    name = co.co_name or '<module>'
    result = {}
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            result.update(extract_with_class(c, path + '/' + name))
    key = path + '/' + name
    result[key] = co
    return result

orig = extract_with_class(code)
co = orig['/<module>/OAuthCallbackHandler/post']
print("=== OAuthCallbackHandler.post (orig) ===")
print("varnames:", co.co_varnames)
dis.dis(co)
