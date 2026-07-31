"""R15 diagnostic: disassemble original pyc vs decompiled OK.py for the 3 mismatched functions."""
import dis
import marshal
import py_compile
import sys
import types
from pathlib import Path

PYC = r"F:/Downloads/pythoncdc-main/site-packages/IQCommon/trade_schedule.pyc"
OK_PY = r"F:/Downloads/pythoncdc-main/site-packages/IQCommon/trade_scheduleOK.py"
OUT_DIR = Path(__file__).parent


def load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract(code, out=None):
    if out is None:
        out = {}
    out[code.co_name or '<module>'] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            extract(c, out)
    return out


def dump(code, fh):
    print(dis.dis(code, file=fh), file=fh)


def main():
    orig = load_pyc_code(PYC)
    orig_map = extract(orig)

    cfile = py_compile.compile(OK_PY, doraise=True, quiet=2)
    with open(cfile, 'rb') as f:
        f.read(16)
        dec_code = marshal.load(f)
    dec_map = extract(dec_code)

    targets = ['get_trading_schedule', 'is_stock_trade_time_now', 'is_future_trade_time_now']
    for fn in targets:
        with open(OUT_DIR / f'_dis_{fn}_orig.txt', 'w', encoding='utf-8') as fh:
            fh.write(f'=== ORIG {fn} ===\n')
            dis.dis(orig_map[fn], file=fh)
        with open(OUT_DIR / f'_dis_{fn}_decomp.txt', 'w', encoding='utf-8') as fh:
            fh.write(f'=== DECOMP {fn} ===\n')
            dis.dis(dec_map[fn], file=fh)
        print(f'wrote _dis_{fn}_orig.txt and _dis_{fn}_decomp.txt')


if __name__ == '__main__':
    main()
