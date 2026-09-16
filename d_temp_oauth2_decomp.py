import sys
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
result = decompile_pyc(pyc)
# Print just the OAuthCallbackHandler class
lines = result.split('\n')
in_class = False
for i, line in enumerate(lines):
    if 'class OAuthCallbackHandler' in line:
        in_class = True
    if in_class:
        print(line)
        if line.startswith('class ') and i > 0 and 'OAuthCallbackHandler' not in line:
            break
