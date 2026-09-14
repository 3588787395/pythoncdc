import sys
sys.path.insert(0, '.')
from core.cfg import decompile
src = '''def f(x, limit):
    while x < limit:
        if x < 0:
            continue
        a = x * 2
        x += 1'''
result = decompile(src)
print(result)
