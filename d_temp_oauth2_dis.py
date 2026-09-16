import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
with open(pyc, 'rb') as f:
    f.read(16); code = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

for name, co in extract(code).items():
    if name == 'post':
        # Find the right post function (HSIDOAuthCallbackHandler)
        print('=== post (from %s) ===' % co.co_filename if hasattr(co, 'co_filename') else '')
        print('co_varnames:', co.co_varnames)
        print('co_consts:', [c for c in co.co_consts if not isinstance(c, types.CodeType)])
        print('\nFull disassembly:')
        dis.dis(co)
        break

# Actually there might be multiple post functions
for name, co in extract(code).items():
    if name == 'post':
        print('\n=== post ===')
        print('co_varnames:', co.co_varnames[:10])
        print('First 5 consts:', [c for c in co.co_consts[:5] if not isinstance(c, types.CodeType)])
        print('Total instructions:', len(list(dis.get_instructions(co))))
