"""R25: dump orig <module> bytecode in a specific offset range with line numbers."""
import sys, types, dis
sys.path.insert(0, '/workspace')
PYC = '/workspace/quotation.pyc'

def load_orig():
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(PYC)
    co = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(co, 'to_python_code'):
        co = co.to_python_code()
    return co

def main():
    import sys
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 780
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 920
    co = load_orig()
    for ins in dis.get_instructions(co):
        if ins.opname == 'CACHE':
            continue
        if lo <= ins.offset <= hi:
            sl = ins.starts_line if ins.starts_line else ''
            print(f"{ins.offset:>5} L{str(sl):>5}  {ins.opname:<22} {ins.argrepr}")

if __name__ == '__main__':
    main()
