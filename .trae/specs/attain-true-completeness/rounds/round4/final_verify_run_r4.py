#!/usr/bin/env python3
"""Round4 主代理终审全量终验编排（基线 = rr-v3r03 = 69132f55 冻结树）。
顺序：regen 0-7 → verify 0-6 + shard7 拆分 → compare×8（vs baseline42）→ small34（拆两半）
→ quotation 单验 → pytest 七套件 → IV.2 门禁自检 → 汇总 summary JSON。
所有子命令超时上限沿用 verify_driver（regen 每文件 90s / verify 290s）。
"""
import json
import os
import subprocess
import sys
import time

ROOT = r'F:\Downloads\pythoncdc-main'
HERE = os.path.join(ROOT, '.trae', 'specs', 'attain-true-completeness', 'rounds', 'round4')
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')
LOG = os.path.join(HERE, 'final_verify_log.txt')
BASE_COMMIT = '69132f55'

SEVEN_TESTS = [
    'tests/test_algorithm_correctness.py',
    'tests/test_deep_nesting_pressure.py',
    'tests/test_control_flow_completeness_matrix.py',
    'tests/test_complete_syntax_coverage.py',
    'tests/test_boundary_cases.py',
    'tests/test_core_functional.py',
    'tests/test_repo_tool_hygiene.py',
]


def sh(args, timeout, label):
    t0 = time.time()
    try:
        r = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=timeout)
        rc, out = r.returncode, (r.stdout or '') + (('\n[stderr] ' + r.stderr) if r.stderr else '')
    except subprocess.TimeoutExpired as e:
        rc, out = 'TIMEOUT', '[TIMEOUT] %s' % str(e)[:300]
    line = '=== %s rc=%s %.1fs' % (label, rc, time.time() - t0)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n' + out[-4000:] + '\n')
    print(line, flush=True)
    return rc, out


def main():
    open(LOG, 'w', encoding='utf-8').close()
    t00 = time.time()
    summary = {}
    # Phase 1: regen 全 8 分片
    for i in range(8):
        sh([sys.executable, os.path.join(HERE, 'verify_driver.py'), 'regen', i], 900, 'REGEN%d' % i)
    # Phase 2: verify 0-6 + compare；shard7 拆分 + compare
    for i in range(7):
        sh([sys.executable, os.path.join(HERE, 'verify_driver.py'), 'verify', i], 320, 'VERIFY%d' % i)
        sh([sys.executable, os.path.join(HERE, 'verify_driver.py'), 'compare', i], 130, 'COMPARE%d' % i)
    sh([sys.executable, os.path.join(HERE, 'verify7_split.py')], 620, 'VERIFY7-SPLIT')
    sh([sys.executable, os.path.join(HERE, 'verify_driver.py'), 'compare', 7], 130, 'COMPARE7')
    # Phase 3: small34 拆两半
    with open(os.path.join(BL, 'failing_index.json'), encoding='utf-8-sig') as f:
        paths34 = [e['path'] for e in json.load(f)]
    reps = []
    for tag, half in zip(('a', 'b'), (paths34[:17], paths34[17:])):
        out = os.path.join(HERE, 'small34_report_%s.json' % tag)
        sh([sys.executable, 'scripts/pyc_verify.py', 'batch', '--json', out] + half,
           300, 'SMALL34-' + tag.upper())
        reps.append(out)
    a = json.load(open(reps[0], encoding='utf-8'))
    b = json.load(open(reps[1], encoding='utf-8'))
    m = dict(a)
    m['rows'] = a.get('rows', []) + b.get('rows', [])
    for k in ('files_total', 'units_total', 'units_success'):
        m[k] = a.get(k, 0) + b.get(k, 0)
    m['success_rate'] = m['units_success'] / m['units_total'] if m['units_total'] else 0.0
    fbs = {}
    for d in (a, b):
        for k, v in d.get('files_by_status', {}).items():
            fbs[k] = fbs.get(k, 0) + v
    m['files_by_status'] = fbs
    pbs = {}
    for d in (a, b):
        for k, v in d.get('paths_by_status', {}).items():
            pbs.setdefault(k, []).extend(v)
    m['paths_by_status'] = pbs
    with open(os.path.join(HERE, 'small34_report_new.json'), 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    sh([sys.executable, 'scripts/pyc_verify.py', 'compare', '--before',
        os.path.join(BL, 'small_test_report.json'), '--after',
        os.path.join(HERE, 'small34_report_new.json')], 130, 'SMALL34-CMP')
    summary['small34'] = {'units_success': m['units_success'], 'units_total': m['units_total'],
                          'files_by_status': m['files_by_status']}
    # Phase 4: quotation 单验
    rc, out = sh([sys.executable, 'scripts/pyc_verify.py', 'single',
                  'site-packages/fly/data/quotation.pyc'], 150, 'QUOTATION')
    summary['quotation'] = {'rc': rc, 'tail': out[-600:]}
    # Phase 5: pytest 七套件
    rc, out = sh([sys.executable, '-X', 'utf8', '-m', 'pytest'] + SEVEN_TESTS +
                 ['-q', '--no-header', '-p', 'no:cacheprovider', '--tb=no'], 300, 'TESTS7')
    lastline = [l for l in out.strip().splitlines() if ('passed' in l or 'failed' in l)]
    summary['pytest'] = {'rc': rc, 'summary_line': lastline[-1] if lastline else out[-200:]}
    # Phase 6: IV.2 自检
    import subprocess as sp
    checks = {}
    r = sp.run([sys.executable, '-X', 'utf8', '-c',
                'import core.cfg.region_analyzer, core.cfg.region_ast_generator, '
                'core.cfg.comprehension_generator, core.cfg.ast_generator_v2, '
                'core.cfg.code_generator, core.cfg.pattern_parser, core.cfg.ast_converter, '
                'core.cfg.exception_handler; print("IMPORT_OK")'],
               cwd=ROOT, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace')
    checks['IMPORT_OK'] = (r.returncode == 0 and 'IMPORT_OK' in (r.stdout or ''))
    r = sp.run([sys.executable, '-X', 'utf8', '-m', 'compileall', '-q', 'core'],
               cwd=ROOT, capture_output=True, text=True, timeout=200, encoding='utf-8', errors='replace')
    checks['COMPILE_OK'] = (r.returncode == 0)
    for path, expect_bom in (('core/cfg/region_ast_generator.py', True),
                             ('core/cfg/region_analyzer.py', True)):
        raw = open(path, 'rb').read(6)
        has = raw.startswith(b'\xef\xbb\xbf')
        single = (raw[:3] == b'\xef\xbb\xbf' and not raw[3:6].startswith(b'\xef\xbb\xbf'))
        checks['BOM_' + os.path.basename(path)] = ('one' if (has == expect_bom and single)
                                                   else 'unexpected:%r' % raw)
    import io as _io
    import tokenize as _tok
    inst = {}
    for path in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py',
                 'core/cfg/ast_generator_v2.py', 'core/cfg/code_generator.py'):
        t = _io.open(path, encoding='utf-8-sig').read().splitlines()
        string_lines = set()
        with open(path, 'rb') as fb:
            src = fb.read().decode('utf-8-sig')
        for tok in _tok.generate_tokens(_io.StringIO(src).readline):
            if tok.type == _tok.STRING:
                for ln in range(tok.start[0], tok.end[0] + 1):
                    string_lines.add(ln)
        code_hits, string_hits = [], []
        for idx, l in enumerate(t, 1):
            s = l.strip()
            if s.startswith('#'):
                continue
            hit = any(k in l for k in ('breakpoint(', 'pdb.set_trace')) or \
                any(tag in l for tag in ('[T]', '[W]', '[G]'))
            if not hit:
                continue
            (string_hits if idx in string_lines else code_hits).append(idx)
        inst[os.path.basename(path)] = {'code': code_hits, 'in_string': string_hits}
    checks['instrumentation_hits'] = inst
    r = sp.run(['git', 'diff', BASE_COMMIT + '..HEAD', '--', 'core/'],
               cwd=ROOT, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace')
    bad_def = [l for l in (r.stdout or '').splitlines()
               if l.startswith('+') and ('def _fix_' in l or 'def _merge_' in l
                                         or 'def _patch_' in l or 'def _fallback_' in l
                                         or 'def _hack_' in l or 'def _workaround_' in l
                                         or 'def _temp_' in l)]
    checks['G3_forbidden_prefix_new_defs'] = len(bad_def)
    summary['iv2'] = checks
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write('=== IV2 ' + json.dumps(checks, ensure_ascii=False) + '\n')
    print('IV2: ' + json.dumps(checks, ensure_ascii=False), flush=True)
    # 汇总
    tot_u = tot_s = tot_f = 0
    shard_rows = []
    for i in range(8):
        try:
            rep = json.load(open(os.path.join(HERE, 'shard%d_report_new.json' % i), encoding='utf-8'))
        except FileNotFoundError:
            shard_rows.append({'shard': i, 'MISSING': True})
            print('shard%d: MISSING' % i, flush=True)
            continue
        tot_u += rep['units_total']; tot_s += rep['units_success']
        tot_f += rep['files_by_status']['failure']
        shard_rows.append({'shard': i, 'files_by_status': rep['files_by_status'],
                           'units_success': rep['units_success'], 'units_total': rep['units_total']})
        print('shard%d: %s units=%s/%s' % (i, rep['files_by_status'],
                                           rep['units_success'], rep['units_total']), flush=True)
    summary['shards'] = shard_rows
    summary['total'] = {'units_success': tot_s, 'units_total': tot_u, 'files_failure': tot_f,
                        'elapsed_sec': round(time.time() - t00, 1)}
    with open(os.path.join(HERE, 'final_verify_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print('FINAL: units=%d/%d files_failure=%d total_elapsed=%.0fs'
          % (tot_s, tot_u, tot_f, time.time() - t00), flush=True)


if __name__ == '__main__':
    main()
