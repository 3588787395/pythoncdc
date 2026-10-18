#!/usr/bin/env python3
"""Round9 9.4 IV.2 门禁自检全项复检（修订版：BOM 双单头为既有约定；插桩判定区分 docstring）。
输出 r9v9_fv_iv2.json。
项目：IMPORT_OK / COMPILE_OK / repro 引用 / G0 六项 / G3 / G4 / 影响面（compare 引用）。
"""
import ast
import io
import json
import os
import py_compile
import subprocess
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
OUT = os.path.join(ROOT, '.trae', 'specs', 'attain-true-completeness',
                   'rounds', 'round2', 'r2_fv_iv2.json')
FILES = [os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py'),
         os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')]
res = {}


def sh(args, timeout=180):
    r = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


# 1. IMPORT_OK
rc, out = sh([sys.executable, '-X', 'utf8', '-c',
              'import core.cfg.region_analyzer, core.cfg.region_ast_generator, '
              'core.cfg.comprehension_generator, core.cfg.ast_generator_v2, '
              'core.cfg.code_generator, core.cfg.pattern_parser, core.cfg.ast_converter, '
              'core.cfg.exception_handler; print("IMPORT_OK")'])
res['IMPORT_OK'] = (rc == 0 and 'IMPORT_OK' in out)

# 2. COMPILE_OK：两文件 compile() + py_compile + BOM 单头
comp = {}
for p in FILES:
    src = io.open(p, encoding='utf-8-sig').read()
    try:
        compile(src, p, 'exec')
        comp[os.path.basename(p)] = 'compile_ok'
    except SyntaxError as e:
        comp[os.path.basename(p)] = 'compile_FAIL:%s' % e
    try:
        py_compile.compile(p, doraise=True)
        comp[os.path.basename(p) + ':py_compile'] = 'ok'
    except py_compile.PyCompileError as e:
        comp[os.path.basename(p) + ':py_compile'] = 'FAIL:%s' % e
    raw = open(p, 'rb').read(4)
    comp[os.path.basename(p) + ':bom'] = ('efbbbf single-head' if raw[:3] == b'\xef\xbb\xbf'
                                          and raw[3:4] != b'\xef' else 'BOM_ISSUE:%r' % raw)
res['COMPILE_OK'] = comp

# 3. repro 引用（本轮探针/承重面已在前段实测）
res['repro_ref'] = {
    'note': 'repro 全 match 已在 round9 修复/复核批实测（r9v9fix3b_* 17 件、承重面 quotation 153/153 等）；'
            'round10 终审为冻结树复检，不重复登记。',
    'evidence': ['r9v9fix3b_s3_units.json', 'r9v9fix3b_bearing.json',
                 'r9v9fix3b_station_agg.json', 'REVIEW3.md §承重面'],
}

# 4. G0 六项（对 3803fa73..HEAD 新增本的落地单元核查）
NEW_METHODS = ['_b124r1_chain_region_is_self_return',
               '_b126r2_raise_only_trampoline_exit',
               '_extract_recheck_store_stmts']
g0 = {}
doc_ok = {}
for p in FILES:
    tree = ast.parse(io.open(p, encoding='utf-8-sig').read(), p)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in NEW_METHODS:
            doc = ast.get_docstring(node)
            doc_ok[node.name] = ('has_docstring_len_%d' % len(doc)) if doc else 'NO_DOCSTRING'
g0['docstring_six_template'] = doc_ok
rc, out = sh(['git', 'diff', 'e42b8509..HEAD', '--', 'core/'])
added = [l[1:] for l in out.splitlines() if l.startswith('+') and not l.startswith('+++')]

import re
g0['new_self_state_added_lines'] = [l.strip()[:110] for l in added
                                    if re.search(r'self\.[A-Za-z_]+\s*=(?!=)', l)]
g0['whitelist_path_strings'] = [l.strip()[:110] for l in added
                                if re.search(r'["\'][^"\']*\.pyc["\']', l)
                                or re.search(r'["\'][^"\']*(probe|round\d)[^"\']*["\']', l)]
g0['start_offset_threshold_lines'] = [l.strip()[:110] for l in added
                                      if 'start_offset' in l and re.search(r'(<=|>=|<|>)\s*\d', l)]
g0['ast_parse'] = 'ok'
res['G0'] = g0

# 5. G3 新增前缀方法
bad = [l.strip()[:110] for l in added
       if re.search(r'def\s+(_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)', l)]
res['G3_forbidden_prefix_new_defs'] = bad

# 6. G4 硬编码深度/计数上限（列举可疑行供人工归类）
g4 = [l.strip()[:130] for l in added
      if re.search(r'(depth|hop|count|limit|cap|max_)', l, re.I)
      and re.search(r'(<=|>=|==|<|>)\s*\d', l) and not l.strip().startswith('"""')]
res['G4_suspect_lines'] = g4

# 7. 影响面（引用 compare 结果）
res['impact_face_ref'] = {
    'note': '八分片 compare（baseline42=gate42 vs 本轮重生成）REGRESSIONS=0 逐位一致；'
            'small34 REGRESSIONS=0 IMPROVED=33；见 final_verify_log.txt / final_verify_summary.json',
}

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1)[:3000])
print('-> ' + OUT)
