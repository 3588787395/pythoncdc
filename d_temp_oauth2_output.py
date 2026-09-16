import sys, types, io, os
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(co, name, parent_name=None):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                if parent_name is None or co.co_name == parent_name:
                    return c
            r = find_code(c, name, parent_name)
            if r: return r
    return None

co = find_code(code, 'post', 'OAuthCallbackHandler')

# Use the actual decompile pipeline
from pycdc import decompile_pyc
full_output = decompile_pyc(pyc)

# Find OAuthCallbackHandler.post  
lines = full_output.split('\n')
in_handler = False
for i, line in enumerate(lines):
    if 'class OAuthCallbackHandler' in line:
        in_handler = True
    if in_handler:
        print(f"{i:4d}: {line}")
        if i > 0 and (line.startswith('class ') and 'OAuthCallbackHandler' not in line):
            break
