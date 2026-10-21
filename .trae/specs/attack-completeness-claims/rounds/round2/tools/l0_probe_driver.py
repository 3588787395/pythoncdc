#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 理论层攻击探针驱动（compile -> pycdc regen -> pyc_verify single）。

用法：
  python -X utf8 l0_probe_driver.py --dir <probes dir> --log <log dir> --stamp <name>

约定（沿用仓库 test_repros/** 的 .py + .pyc + ...OK.py 同目录约定）：
  <name>.py        探针源
  <name>.pyc       py_compile 产物（与源同目录、同名）
  <name>OK.py      pycdc.py -o 产物
  judge: python -X utf8 scripts/pyc_verify.py single <name>.pyc --source <name>OK.py

纪律：不写 core/**、tests/**、wiki/**；命令 ≤300s；输出 JSON 落 log 目录。
"""
import hashlib
import json
import os
import py_compile
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))


def sha256(path, n=16):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:n]


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, cwd=ROOT, timeout=timeout,
                           encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def parse_status(out):
    status, us, ut = None, None, None
    fails = []
    for line in out.splitlines():
        s = line.strip()
        if '[single] status=' in s:
            seg = s.split('status=', 1)[1].split()
            status = seg[0]
            for tok in seg:
                if tok.startswith('units='):
                    a, b = tok[len('units='):].split('/')
                    us, ut = int(a), int(b)
        elif s.startswith('***'):
            fails.append(s)
    return status, us, ut, fails


def one(name, srcdir, timeout=290):
    src = os.path.join(srcdir, name)
    pyc = os.path.abspath(src[:-3] + '.pyc')
    ok = os.path.abspath(src[:-3] + 'OK.py')
    rec = {'name': name, 'src': os.path.relpath(src, ROOT).replace('\\', '/')}
    try:
        py_compile.compile(src, cfile=pyc, doraise=True, optimize=0)
    except Exception as exc:
        rec['status'] = 'compile_error_src'
        rec['detail'] = '%s: %s' % (type(exc).__name__, exc)
        return rec
    rec['pyc'] = os.path.relpath(pyc, ROOT).replace('\\', '/')
    rec['pyc_sha'] = sha256(pyc)
    rc, out = run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'pycdc.py'),
                   pyc, '-o', ok], timeout=timeout)
    rec['regen_rc'] = rc
    rec['regen_tail'] = out.strip()[-500:]
    rec['ok_exists'] = os.path.isfile(ok)
    if not rec['ok_exists']:
        rec['status'] = 'no_product'
        rec['units_success'] = None
        rec['units_total'] = None
        rec['failures'] = []
        return rec
    rec['ok_sha'] = sha256(ok)
    with open(ok, encoding='utf-8', errors='replace') as f:
        rec['ok_text'] = f.read()
    rc2, out2 = run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                     'single', pyc, '--source', ok], timeout=timeout)
    rec['verify_rc'] = rc2
    status, us, ut, fails = parse_status(out2)
    rec['status'] = status
    rec['units_success'] = us
    rec['units_total'] = ut
    rec['failures'] = fails
    rec['verify_tail'] = out2.strip()[-900:]
    return rec


def main():
    args = sys.argv[1:]
    srcdir = None
    logdir = None
    stamp = 'default'
    only = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--dir':
            srcdir = args[i + 1]; i += 2
        elif a == '--log':
            logdir = args[i + 1]; i += 2
        elif a == '--stamp':
            stamp = args[i + 1]; i += 2
        else:
            only.append(a); i += 1
    if not srcdir or not logdir:
        print(__doc__)
        return 2
    srcdir = os.path.abspath(srcdir)
    os.makedirs(logdir, exist_ok=True)
    names = sorted(n for n in os.listdir(srcdir)
                   if n.endswith('.py') and not n.endswith('OK.py'))
    if only:
        names = [n for n in names if any(o in n for o in only)]
    rows = []
    t0 = time.time()
    for n in names:
        r = one(n, srcdir)
        rows.append(r)
        print('[%s] regen_rc=%s status=%s units=%s/%s' % (
            n, r.get('regen_rc'), r.get('status'),
            r.get('units_success'), r.get('units_total')), flush=True)
        for f in (r.get('failures') or []):
            print('    ' + f, flush=True)
    out = os.path.join(logdir, 'l0_probes_%s.json' % stamp)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                   'elapsed_sec': round(time.time() - t0, 1),
                   'probes': rows}, f, ensure_ascii=False, indent=1)
    ok = sum(r.get('units_success') or 0 for r in rows)
    tot = sum(r.get('units_total') or 0 for r in rows)
    nf = sum(1 for r in rows if r.get('status') != 'success')
    print('-> probes=%d units=%d/%d non_success_files=%d  %s' % (
        len(rows), ok, tot, nf, os.path.basename(out)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
