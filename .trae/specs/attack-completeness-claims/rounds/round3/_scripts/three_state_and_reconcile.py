# -*- coding: utf-8 -*-
"""three_state_and_reconcile.py — L1 口径层：§4 三态分类审计 + §6 与判定空间的差距对账

(a) 三态的**测点存在性**审计：仓内是否存在任何工具把形态判成 完备/破口/零能力
    （grep 全仓 .py，找三态关键字与状态判定式）；
(b) 判定空间 39 形态 vs 25 行：哪些形态有行、哪些没有（NEW 族）；
(c) §6 对账：round1 覆盖基线读数 vs 本轮 §3/§5 读数。
"""
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = ROOT / '.trae' / 'specs' / 'attack-completeness-claims' / 'rounds' / 'round3' / '_out'
OUT.mkdir(parents=True, exist_ok=True)
REPO = ROOT / '.trae' / 'specs' / 'attack-completeness-claims'

rep = {}

# ---------- (a) 三态测点存在性 ----------
tri = []
for p in list(ROOT.rglob('*.py')):
    sp = p.as_posix()
    if '/.git/' in sp or '__pycache__' in sp:
        continue
    if sp.startswith((ROOT / '.trae').as_posix()):
        continue   # 规范/证据目录不是实现测点
    try:
        t = p.read_text(encoding='utf-8', errors='replace')
    except OSError:
        continue
    hits = {k: len(re.findall(k, t)) for k in ('完备', '破口', '零能力')}
    if any(hits.values()):
        tri.append({'file': p.relative_to(ROOT).as_posix(), 'hits': hits})
rep['impl_files_mentioning_three_states'] = tri
rep['impl_files_with_state_assignment'] = [
    x for x in tri if re.search(r"(完备|破口|零能力)\s*=", x['file'] and
                                 (ROOT / x['file']).read_text(encoding='utf-8', errors='replace'))]

# ---------- (b) 39 形态 vs 25 行 ----------
space = json.load(io.open(REPO / 'rounds' / 'round1' / 'judgment_space.json', encoding='utf-8'))
forms = sorted({e['form'] for e in space['entries']})
rows_of_form = {}
for e in space['entries']:
    rows_of_form.setdefault(e['form'], e.get('row'))
with_row = sorted(f for f in forms if rows_of_form.get(f) and rows_of_form[f] != 'NEW')
new_only = sorted(f for f in forms if rows_of_form.get(f) == 'NEW')
rep['space_forms_total'] = len(forms)
rep['space_forms_with_25row'] = len(with_row)
rep['space_forms_NEW_no_row'] = len(new_only)
rep['space_forms_NEW_list'] = new_only

# ---------- (c) 对账 ----------
cov = json.load(io.open(REPO / 'rounds' / 'round1' / 'coverage_baseline.json', encoding='utf-8'))
rep['round1_coverage_totals'] = cov['totals']
vq = json.load(io.open(OUT / 'variant_quantify.json', encoding='utf-8'))
rep['round3_variant_totals'] = vq['totals']
rep['round3_space_dimensions'] = {
    'entries': vq['space_entries'], 'forms': vq['space_forms'],
    'form_variant_pairs': vq['space_form_variant_pairs'],
    'form_variant_host_triples': vq['space_form_variant_host_triples'],
}
den = json.load(io.open(OUT / 'denominator_audit.json', encoding='utf-8'))
num = json.load(io.open(OUT / 'numerator_lexical_audit.json', encoding='utf-8'))
rep['denominator_summary'] = {
    'tool_rule_denominator': den['tool_denominator_size'],
    'published_denominator': den['published_denominator'],
    'true_syntactic_surface': den['true_syntactic_surface_size'],
    'missing_lowercase_syntax_classes': den['lowercase_syntax_dropped'],
    'missing_never_recovered': den['dropped_and_never_recovered'],
    'denominator_extra_non_syntax': len(den['denominator_minus_true_syntactic']),
    'token_classes': len(den['token_classes_in_denominator']),
    'ctx_classes': len(den['ctx_classes_in_denominator']),
    'simulated_312_denominator': den['simulated_312_denominator_size'],
    'simulated_312_added': den['simulated_312_added'],
    'extra_forms_with_overlap': num['extra_forms_count_with_denominator_overlap'],
}
rep['numerator_summary'] = {
    'raw': num['ast_numerator_raw'],
    'code_only_strict': num['ast_numerator_code_only_strict'],
    'tier_counts': num['tier_counts'],
    'extra_forms_raw': num['extra_forms_raw_count'],
    'extra_forms_comment_only': num['extra_forms_only_via_comment_or_string'],
}

o = OUT / 'three_state_and_reconcile.json'
io.open(o, 'w', encoding='utf-8', newline='\n').write(json.dumps(rep, ensure_ascii=False, indent=2))
print(json.dumps(rep, ensure_ascii=False, indent=1)[:4000])
print('JSON ->', o)
