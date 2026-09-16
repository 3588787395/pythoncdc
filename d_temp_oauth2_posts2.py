import sys, types, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find both post code objects
def find_all_posts(co, path=''):
    name = co.co_name or '<module>'
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            find_all_posts(c, path + '/' + name)
    if co.co_name == 'post':
        print(f"\n=== post at {path}/{name} ===")
        print(f"varnames: {co.co_varnames[:5]}")
        # Count instructions
        import dis
        instrs = list(dis.get_instructions(co))
        print(f"Total instructions: {len(instrs)}")
        # Check if offset 140 exists
        for inst in instrs:
            if inst.offset == 140:
                print(f"Offset 140: {inst.opname} {inst.argval}")
                break

find_all_posts(code)
