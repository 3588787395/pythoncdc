#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 1 探针驱动（只读侦察轮）——RV2 口径：先 regen（pycdc -o）再 verify single。

纪律：不动 core/**、不动 wiki/**、不改 tests/**、不 git 写操作。
所有探针副本与产物落在本规范目录 `test_repros/round1/`（stage），
源树 test_repros/ 的原件只读引用（拷贝进 stage 后运行，绝不回写源树）。

用法：
  python -X utf8 rec1_run.py --stage <dir> --log <dir> --stamp <name> \
      name1=test_repros/round3/e07_g4_star_slice_containers.pyc [name2=...]

每个 entry 输出：
  [name] regen_rc=<rc> status=<success|failure|compile_error|error> units=U/T
输出 JSON：<log>/rec1_probes_<stamp>.json（含每个探针的完整 stdout/stderr 文本与 sha）。
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
STAT_RE = None


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
        line_strip = line.strip()
        if '[single] status=' in line_strip:
            seg = line_strip.split('status=', 1)[1].split()
            status = seg[0]
            for tok in seg:
                if tok.startswith('units='):
                    a, b = tok[len('units='):].split('/')
                    us, ut = int(a), int(b)
        elif line_strip.startswith('***') and 'Failure' in line_strip:
            fails.append(line_strip)
        elif line_strip.startswith('***') and 'Different' in line_strip:
            fails.append(line_strip)
        elif line_strip.startswith('***') and 'Missing' in line_strip:
            fails.append(line_strip)
        elif line_strip.startswith('***') and 'Extra' in line_strip:
            fails.append(line_strip)
    return status, us, ut, fails


def one(name, rel, stage, logdir, regen_timeout=240, verify_timeout=290):
    if rel.startswith('@'):
        # 已在 stage 内的本地探针（自建：源+.pyc 同放 stage）
        staged_pyc = os.path.join(stage, os.path.basename(rel[1:]))
        if not os.path.isfile(staged_pyc):
            return {'name': name, 'pyc': rel, 'error': 'staged pyc 不存在: %s' % staged_pyc}
        src_pyc = staged_pyc
    else:
        src_pyc = os.path.join(ROOT, rel.replace('/', os.sep))
        if not os.path.isfile(src_pyc):
            return {'name': name, 'pyc': rel, 'error': 'pyc 不存在'}
        base = os.path.basename(src_pyc)
        staged_pyc = os.path.join(stage, 'rec1_%s_%s' % (name, base))
        if not staged_pyc.lower().endswith('.pyc'):
            staged_pyc += '.pyc'
        shutil.copyfile(src_pyc, staged_pyc)
    ok_path = staged_pyc[:-4] + 'OK.py'
    rec = {'name': name, 'pyc_src_rel': rel, 'pyc_src_sha': sha256(src_pyc),
           'staged_pyc': os.path.relpath(staged_pyc, ROOT).replace('\\', '/'),
           'mtime': time.strftime('%Y-%m-%dT%H:%M:%S')}
    rc_regen, regen_out = run([sys.executable, '-X', 'utf8',
                               os.path.join(ROOT, 'pycdc.py'), staged_pyc, '-o', ok_path],
                              timeout=regen_timeout)
    rec['regen_rc'] = rc_regen
    rec['regen_tail'] = regen_out.strip()[-800:]
    rec['ok_exists'] = os.path.isfile(ok_path)
    if rec['ok_exists']:
        rec['ok_sha'] = sha256(ok_path)
        # 独立编译检查（即便 verify 抓 compile_error，也留独立证据）
        with open(ok_path, encoding='utf-8', errors='replace') as f:
            rec['ok_text'] = f.read()
    if rec['regen_rc'] == -9:
        # regen 挂死（HANG）：判据引擎同源，verify 不再空转
        rec['verify_rc'] = None
        rec['verify_out'] = 'SKIPPED: regen HANG(%ss)' % regen_timeout
        rec['status'] = 'hang'
        rec['units_success'] = None
        rec['units_total'] = None
        rec['failures'] = []
        return rec
    rc_v, out_v = run([sys.executable, '-X', 'utf8',
                       os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                       'single', staged_pyc], timeout=verify_timeout)
    rec['verify_rc'] = rc_v
    rec['verify_out'] = out_v.strip()
    status, us, ut, fails = parse_status(out_v)
    rec['status'] = status
    rec['units_success'] = us
    rec['units_total'] = ut
    rec['failures'] = fails
    return rec


def main():
    args = sys.argv[1:]
    stage = None
    logdir = None
    stamp = 'default'
    pairs = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--stage':
            stage = args[i + 1]; i += 2
        elif a == '--log':
            logdir = args[i + 1]; i += 2
        elif a == '--stamp':
            stamp = args[i + 1]; i += 2
        else:
            name, _, rel = a.partition('=')
            to = None
            import re as _re
            m = _re.search(r'#T(\d+)$', rel)
            if m:
                to = int(m.group(1)); rel = rel[:m.start()]
            pairs.append((name, rel, to)); i += 1
    if not stage or not logdir or not pairs:
        print(__doc__)
        return 2
    os.makedirs(stage, exist_ok=True)
    os.makedirs(logdir, exist_ok=True)
    rows = []
    for name, rel, to in pairs:
        r = one(name, rel, stage, logdir,
                regen_timeout=(to or 240), verify_timeout=(to or 290))
        rows.append(r)
        print('[%s] regen_rc=%s status=%s units=%s/%s' % (
            name, r.get('regen_rc'), r.get('status'),
            r.get('units_success'), r.get('units_total')), flush=True)
        for f in (r.get('failures') or []):
            print('    ' + f, flush=True)
    out = os.path.join(logdir, 'rec1_probes_%s.json' % stamp)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    ok = sum(r.get('units_success') or 0 for r in rows)
    tot = sum(r.get('units_total') or 0 for r in rows)
    print('-> units=%d/%d  (%d probes)  %s' % (ok, tot, len(rows), os.path.basename(out)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
