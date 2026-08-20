"""Test: what does Python 3.11.7 compile break in try-for as?"""
import dis

src = '''
def f(data):
    try:
        for item in data:
            if item > 100:
                break
    except Exception:
        pass
'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'f':
        dis.dis(c)
        break
