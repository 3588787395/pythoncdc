import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import decompile
def test(src, label):
    out = decompile(src, filename='<s>', use_region=True)
    print("==", label, "==")
    print(out)
    print("---")
test('''
def g(a):
    a = a
    return a
''', "func x=x")
test('''
def g():
    TickBar = TickBar
    BarData = BarData
    return 1
''', "func alias")
test('''
class C:
    X = X
    def m(self):
        return 1
''', "class alias")
