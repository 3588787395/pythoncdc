# -*- coding: utf-8 -*-
"""variant_quantify.py — L1 口径层：粒度错配量化 + 「单元绿 ⇒ 完备」推断链的变体级核验

数据源：
  - 判定空间：rounds/round1/judgment_space.json（39 形态族 / 1556 条目）
  - 变体谓词：tools/completeness/jspace_generator.py::build_families()（生成器内的 AST 谓词）
  - 25 行登记：.trae/specs/attain-true-completeness/rounds/round8/REVIEW.md §2
  - 探针源：test_repros/**/<probe>.py（用 python ast 解析，不用 grep）

产出：
  1) (form,variant) / (form,variant,host) / 条目 三级计数 vs 128 分母
  2) 逐行：声明变体数 / 由该行**登记探针**实际触发的变体数 / 触发的变体名
  3) 逐行：判定空间证据索引中触发的变体数（对照）
"""
import ast as pyast
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = ROOT / '.trae' / 'specs' / 'attack-completeness-claims' / 'rounds' / 'round3' / '_out'
OUT.mkdir(parents=True, exist_ok=True)
REPO = ROOT / '.trae' / 'specs' / 'attack-completeness-claims'
PRIOR = ROOT / '.trae' / 'specs' / 'attain-true-completeness'

sys.path.insert(0, str(ROOT / 'tools' / 'completeness'))
import jspace_generator as JG  # noqa: E402


def parse_review_rows():
    """从 REVIEW.md §2 表读 25 行：(序号, 行名, 登记探针相对路径, 单元读数)。"""
    txt = (PRIOR / 'rounds' / 'round8' / 'REVIEW.md').read_text(encoding='utf-8')
    rows = []
    in_sec2 = False
    for line in txt.splitlines():
        if line.startswith('## §2'):
            in_sec2 = True
            continue
        if in_sec2 and line.startswith('## §3'):
            break
        if not in_sec2:
            continue
        m = re.match(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|', line)
        if not m:
            continue
        num, name, probe_cell, units, neg, verdict = m.groups()
        probes = re.findall(r'`([^`]+)`', probe_cell)
        rows.append({
            'no': int(num), 'row': name.strip(), 'probe_cell': probe_cell.strip(),
            'probe_refs': probes, 'units': units.strip(), 'verdict': verdict.strip(),
        })
    return rows


def resolve_probe(ref, extra_roots=()):
    """把 REVIEW.md 里的探针引用解析为仓内 <stem>.py 源文件（探针 .py 与 .pyc 同目录）。"""
    ref = ref.strip().replace('\\', '/')
    stem = ref[:-4] if ref.endswith('.pyc') else ref
    name = stem.split('/')[-1]
    cands = []
    roots = [ROOT] + list(extra_roots)
    for base in roots:
        for p in base.rglob(name + '.py'):
            sp = p.as_posix()
            if '/.git/' in sp or '__pycache__' in sp:
                continue
            cands.append(p)
    return sorted(set(cands))


def node_contexts(tree):
    """复刻 jspace_generator._Walker：返回 (node, parent, ancestors) 列表。"""
    out = []
    stack = []

    def visit(node):
        stack.append(node)
        parent = stack[-2] if len(stack) > 1 else None
        out.append((node, parent, list(stack[:-1])))
        for child in pyast.iter_child_nodes(node):
            visit(child)
        stack.pop()

    visit(tree)
    return out


def variant_hits(src_path, family):
    """在给定源码里计算该族各变体谓词是否被触发。"""
    try:
        tree = pyast.parse(src_path.read_text(encoding='utf-8', errors='replace'))
    except Exception as e:
        return None, str(e)
    ctxs = node_contexts(tree)
    hits = set()
    for vname, _note, pred in family['variants']:
        for node, parent, anc in ctxs:
            if not isinstance(node, family['nodes']):
                continue
            c = JG._Ctx(node, parent, anc)
            try:
                if pred(c):
                    hits.add(vname)
                    break
            except Exception:
                pass
    return hits, None


def form_presence(src_path, family):
    """登记探针里是否出现该行的**声明形态节点**（family['nodes'] 的任一实例）。
    这是 F1 的同构判据：行名声明的形态在证据中零出现。"""
    try:
        tree = pyast.parse(src_path.read_text(encoding='utf-8', errors='replace'))
    except Exception as e:
        return None, str(e)
    n = 0
    for node in pyast.walk(tree):
        if isinstance(node, family['nodes']):
            n += 1
    return n, None


def main():
    space = json.load(io.open(REPO / 'rounds' / 'round1' / 'judgment_space.json', encoding='utf-8'))
    fams = JG.build_families()
    fam_by_code = {f['code']: f for f in fams}
    entries = space['entries']

    # ---------- §3 粒度量化 ----------
    pairs = {(f, v) for e in entries for f, v in [(e['form'], e['variant'])]}
    triples = {(e['form'], e['variant'], e['host']) for e in entries}
    forms = sorted({e['form'] for e in entries})
    variants_by_form = {}
    for e in entries:
        variants_by_form.setdefault(e['form'], set()).add(e['variant'])
    hosts_by_form = {}
    for e in entries:
        hosts_by_form.setdefault(e['form'], set()).add(e['host'])

    # ---------- §5 逐行核验 ----------
    rows = parse_review_rows()
    index = JG.build_evidence_index(str(PRIOR / 'rounds'))
    # 证据索引 -> (rel, name) -> 源文本
    evidence_src = {}
    for (rel, name), rec in index.items():
        ok = rec.get('ok_text') or ''
        evidence_src[(rel, name)] = ok

    row_results = []
    for r in rows:
        row = r['row']
        # 该行对应的形态族（族 row 字段 == 行名）
        fams_for_row = [f for f in fams if f.get('row') == row]
        declared = []
        for f in fams_for_row:
            for vname, note, _p in f['variants']:
                declared.append((f['code'], vname, note))
        # 登记探针
        probes = []
        for ref in r['probe_refs']:
            probes += resolve_probe(ref)
        probes = sorted(set(probes))
        exercised = set()
        exercised_detail = {}
        for p in probes:
            for f in fams_for_row:
                hits, err = variant_hits(p, f)
                if hits is None:
                    exercised_detail.setdefault(p.name, {})['ERROR'] = err
                    continue
                for h in hits:
                    exercised.add((f['code'], h))
                exercised_detail.setdefault(p.name, {})[f['code']] = sorted(hits)
        # 判定空间证据索引内触发的变体（对照）
        space_hits = set()
        for (rel, name), ok in evidence_src.items():
            try:
                tree = pyast.parse(ok)
            except Exception:
                continue
            for node, parent, anc in node_contexts(tree):
                for f in fams_for_row:
                    if not isinstance(node, f['nodes']):
                        continue
                    c = JG._Ctx(node, parent, anc)
                    for vname, _n, pred in f['variants']:
                        try:
                            if pred(c):
                                space_hits.add((f['code'], vname))
                        except Exception:
                            pass
        declared_set = {(c, v) for c, v, _n in declared}
        # F1 同构判据：登记探针中该行声明形态的节点出现次数
        presence = {}
        for p in probes:
            for f in fams_for_row:
                cnt, err = form_presence(p, f)
                if cnt is None:
                    presence.setdefault(p.name, {})['ERROR'] = err
                    continue
                presence.setdefault(p.name, {})[f['code']] = cnt
        form_node_total = sum(
            v for fk, fv in presence.items() for ck, v in fv.items()
            if isinstance(v, int) and not ck.startswith('ERROR'))
        row_results.append({
            'no': r['no'], 'row': row, 'units': r['units'], 'verdict': r['verdict'],
            'probe_refs': r['probe_refs'],
            'probe_files': [p.relative_to(ROOT).as_posix() for p in probes],
            'probe_missing': [ref for ref in r['probe_refs'] if not resolve_probe(ref)],
            'families': [f['code'] for f in fams_for_row],
            'declared_variants': len(declared_set),
            'declared_variant_list': sorted('%s/%s' % (c, v) for c, v in declared_set),
            'exercised_by_registered_probe': len(declared_set & exercised),
            'exercised_missing': sorted('%s/%s' % (c, v) for c, v in (declared_set - exercised)),
            'exercised_by_space_evidence': len(declared_set & space_hits),
            'space_only_missing': sorted('%s/%s' % (c, v) for c, v in (declared_set - space_hits)),
            'form_node_instances_in_probe': form_node_total,
            'f1_class_form_absent': form_node_total == 0 and bool(probes),
            'detail': {k: v for k, v in exercised_detail.items()},
            'presence': presence,
        })

    out = {
        'space_entries': len(entries),
        'space_forms': len(forms),
        'space_form_variant_pairs': len(pairs),
        'space_form_variant_host_triples': len(triples),
        'denominator_claim': 128,
        'per_form': {f: {'variants': len(variants_by_form[f]),
                         'hosts': len(hosts_by_form[f]),
                         'entries': sum(1 for e in entries if e['form'] == f)}
                     for f in forms},
        'rows': row_results,
        'totals': {
            'rows': len(row_results),
            'declared_variants_total': sum(x['declared_variants'] for x in row_results),
            'exercised_by_registered_probe_total': sum(x['exercised_by_registered_probe'] for x in row_results),
            'exercised_by_space_evidence_total': sum(x['exercised_by_space_evidence'] for x in row_results),
            'rows_with_gap': sum(1 for x in row_results if x['exercised_by_registered_probe'] < x['declared_variants']),
            'rows_with_zero_exercised': sum(1 for x in row_results if x['exercised_by_registered_probe'] == 0),
            'rows_f1_class_form_absent': sum(1 for x in row_results if x['f1_class_form_absent']),
            'f1_class_rows': [x['row'] for x in row_results if x['f1_class_form_absent']],
        },
    }
    o = OUT / 'variant_quantify.json'
    io.open(o, 'w', encoding='utf-8', newline='\n').write(json.dumps(out, ensure_ascii=False, indent=2))

    print('判定空间条目 %d / 形态 %d / (form,variant) %d / (form,variant,host) %d  vs 分母 128'
          % (len(entries), len(forms), len(pairs), len(triples)))
    t = out['totals']
    print('25 行：声明变体合计 %d；登记探针实际触发 %d；判定空间证据触发 %d'
          % (t['declared_variants_total'], t['exercised_by_registered_probe_total'], t['exercised_by_space_evidence_total']))
    print('有变体触发缺口的行数：%d / %d（其中 0 触发行：%d）'
          % (t['rows_with_gap'], t['rows'], t['rows_with_zero_exercised']))
    print('F1 同构行（登记探针中该行形态节点出现 0 次）：%d 行 %s'
          % (t['rows_f1_class_form_absent'], t['f1_class_rows']))
    print()
    print('%-3s %-18s %5s %5s %5s %5s  %s'
          % ('#', 'row', '声明', '探针', '空间', '形态节点', '缺变体(登记探针未触发)'))
    for x in row_results:
        print('%-3d %-18s %5d %5d %5d %5d  %s'
              % (x['no'], x['row'], x['declared_variants'], x['exercised_by_registered_probe'],
                 x['exercised_by_space_evidence'], x['form_node_instances_in_probe'],
                 ','.join(x['exercised_missing'][:6])[:110]))
        if x['probe_missing']:
            print('    ! 探针未解析: %s' % x['probe_missing'])
    print('JSON ->', o)


if __name__ == '__main__':
    main()
