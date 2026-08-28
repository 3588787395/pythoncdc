import sys; sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from core.cfg import decompile
def show(src):
    print("=== SRC ===")
    print(src)
    print("--- OUT ---")
    print(decompile(src, '<t>'))
    print()
show('''def f(a, c, b):
    x = a if c else b
    y = 1
    return y
''')
show('''def f(self, p, c):
    self.x = p if c else 0
    self.y = 1
    return self.y
''')
show('''def f(self, p, c):
    self.x = p if c else 0
    return self.x
''')
