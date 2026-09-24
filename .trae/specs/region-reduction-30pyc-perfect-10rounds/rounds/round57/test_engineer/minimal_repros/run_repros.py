# R57 最小复现批量运行器 (round57 test_engineer)
# 流程: py_compile 编译 repro -> pycdc.decompile_pyc 反编译 -> 重编译 ->
# 复用 _r10_strict_check.py 逐函数严格比较 -> 输出 MATCH/MISMATCH + repro_results.jsonl
import io
import json
import marshal
import py_compile
import sys
import traceback
from pathlib import Path

ROOT = Path(r'F:\Downloads\pythoncdc-main')
sys.path.insert(0, str(ROOT))
TMP = Path(r'D:\Temp\opencode\r57t\repro_out')
TMP.mkdir(parents=True, exist_ok=True)
REPRO_DIR = Path(__file__).resolve().parent

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pycdc import decompile_pyc
import _r10_strict_check as SC


def code_map(code):
    out = {}

    def walk(c, prefix=''):
        key = prefix + c.co_name
        out.setdefault(key, c)
        for k in c.co_consts:
            if hasattr(k, 'co_name'):
                walk(k, key + '.')

    walk(code)
    return out


def run_one(py_path):
    rec = {'file': py_path.name, 'status': None, 'defects': [], 'error': None}
    try:
        pyc = TMP / (py_path.stem + '.pyc')
        py_compile.compile(str(py_path), cfile=str(pyc), doraise=True, quiet=2)
        with open(pyc, 'rb') as f:
            f.read(16)
            code_orig = marshal.load(f)
        src = decompile_pyc(str(pyc))
        dec_py = TMP / (py_path.stem + '_dec.py')
        dec_py.write_text(src, encoding='utf-8')
        code_dec = compile(src, str(dec_py), 'exec')
        mo, md = code_map(code_orig), code_map(code_dec)
        names = sorted(set(mo) & set(md))
        rec['functions'] = len(names)
        for n in names:
            kind, msg, _ = SC.strict_compare(mo[n], md[n])
            if kind:
                rec['defects'].append({'fn': n, 'kind': kind, 'msg': msg})
        missing = sorted(set(mo) - set(md))
        if missing:
            rec['missing_functions'] = missing
        extra = sorted(set(md) - set(mo))
        if extra:
            rec['extra_functions'] = extra
        bad = len(rec['defects']) + len(missing) + len(extra)
        rec['status'] = 'MATCH' if bad == 0 else 'MISMATCH'
    except Exception as e:
        rec['status'] = 'ERROR'
        rec['error'] = '%s: %s' % (type(e).__name__, e)
        rec['traceback'] = traceback.format_exc(limit=4)
    return rec


def main():
    repros = sorted(REPRO_DIR.glob('r57_*.py'))
    repros = [p for p in repros if p.name != 'run_repros.py']
    results = []
    for p in repros:
        rec = run_one(p)
        results.append(rec)
        tag = rec['status']
        line = '%-52s %s' % (p.name, tag)
        if rec['defects']:
            d = rec['defects'][0]
            line += '  [%s] %s: %s' % (d['kind'], d['fn'], d['msg'])
        elif rec.get('missing_functions') or rec.get('extra_functions'):
            line += '  [fn-set] missing=%s extra=%s' % (
                rec.get('missing_functions'), rec.get('extra_functions'))
        elif rec.get('error'):
            line += '  %s' % rec['error']
        print(line, flush=True)
    out_jsonl = REPRO_DIR / 'repro_results.jsonl'
    with open(out_jsonl, 'w', encoding='utf-8') as f:
        for rec in results:
            f.write(json.dumps(rec, ensure_ascii=True) + '\n')
    n_mis = sum(1 for r in results if r['status'] == 'MISMATCH')
    n_match = sum(1 for r in results if r['status'] == 'MATCH')
    n_err = sum(1 for r in results if r['status'] == 'ERROR')
    print('\nsummary: total=%d MISMATCH=%d MATCH=%d ERROR=%d' % (
        len(results), n_mis, n_match, n_err))
    print('results written to %s' % out_jsonl)
    return 0


if __name__ == '__main__':
    sys.exit(main())
