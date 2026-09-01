import sys, dis
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import decompile

srcs = {
 'repro_01': '''
class DataProxy:
    TickBar = TickBar
    BarData = BarData

    def __init__(self):
        self.a = 1
''',
 'repro_11': '''
class C:
    X = X

    def m(self):
        return 1
''',
 'repro_02': '''
def f(items):
    for i in items:
        if i > 0:
            break
    else:
        return None
    return i
''',
 'repro_04': '''
def setup(self, engine):
    if engine.config.other.enable_debug:
        import ptvsd
        if get_python_version() == '3.11':
            ptvsd.reset()
        engine.config.other.enable_debug = config.timeout or 10
''',
}

for name, src in srcs.items():
    co = compile(src, '<string>', 'exec')
    print("="*60)
    print(name)
    print("--- ORIG ---")
    dis.dis(co)
    print("--- DECOMPILED ---")
    out = decompile(src, filename='<string>', use_region=True)
    print(out)
    dec = compile(out, '<decomp>', 'exec')
    print("--- DECOMPILED BYTECODE ---")
    dis.dis(dec)
