import sys
sys.path.insert(0, '.')
from core.cfg import decompile
src = '''x=0
while x<10: x+=1
else: print('done')'''
result = decompile(src)
print(repr(result))
