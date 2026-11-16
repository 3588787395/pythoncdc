# -*- coding: utf-8 -*-
"""R7 29-entry deep triage: walk the nested code-object tree of the original
pyc and of the recompiled product source, and report every difference at its
own path, with constant-pool order/identity analysis and instruction diffs.

Read-only analysis.  Writes JSON + a readable log under fresh/gate_r7/.
"""
from __future__ import annotations

import collections
import dis
import hashlib
import io
import json
import marshal
import os
import sys
import types

ROOT = r'F:\Downloads\pythoncdc-main'
EV = r'D:\temp\opencode\cl_layout\gap\g3fix\semantic_v3m_b275_g3fix_merged.json'
TR = r'D:\temp\opencode\cl_layout\gap\g3gap\r7_transfer.json'
OUT_JSON = os.path.join(ROOT, 'fresh', 'gate_r7', 'r7_deep_diff.json')
OUT_LOG = os.path.join(ROOT, 'fresh', 'gate_r7', 'r7_deep_diff.log')


def load_pyc_code(path):
    data = open(path, 'rb').read()
    return marshal.loads(data[16:])


def load_src_code(path):
    text = open(path, 'r', encoding='utf-8-sig', errors='replace').read()
    # dont_inherit=True mirrors SourceFileLoader.get_code -> source_to_code, which
    # is what semantic_diff._load_target uses for the product side.  Without it the
    # caller's `from __future__ import annotations` leaks in as CO_FUTURE_ANNOTATIONS
    # (0x1000000) and fabricates a co_flags difference on every code object.
    return compile(text, path, 'exec', dont_inherit=True)


def const_key(value):
    """Stable identity of a constant: type + repr (code objects by qualname)."""
    if isinstance(value, types.CodeType):
        return ('code', value.co_qualname)
    return (type(value).__name__, repr(value))


def value_key(value):
    """Equality-only identity (ignores type): used to spot 0 vs False."""
    if isinstance(value, types.CodeType):
        return ('code', value.co_qualname)
    try:
        if value == 0 and not isinstance(value, (str, bytes)):
            return ('zero-ish',)
        if value is True or value == 1:
            return ('one-ish',)
    except BaseException:
        pass
    return ('val', repr(value))


def const_sig(value, depth=0):
    if isinstance(value, types.CodeType):
        return {'t': 'code', 'qualname': value.co_qualname,
                'code_sha': hashlib.sha256(value.co_code).hexdigest()[:12],
                'consts_len': len(value.co_consts)}
    if isinstance(value, tuple):
        return {'t': 'tuple', 'v': [const_sig(item, depth + 1) for item in value]}
    if isinstance(value, frozenset):
        return {'t': 'frozenset', 'v': sorted((const_sig(i, depth + 1) for i in value),
                                              key=lambda x: json.dumps(x, sort_keys=True))}
    return {'t': type(value).__name__, 'repr': repr(value)}


def short(value, limit=60):
    text = repr(value) if not isinstance(value, types.CodeType) else '<code %s>' % value.co_qualname
    return text if len(text) <= limit else text[:limit - 3] + '...'


def instrs(code):
    out = []
    for ins in dis.get_instructions(code):
        arg = ins.arg
        av = ins.argval
        if isinstance(av, types.CodeType):
            av = '<code %s>' % av.co_qualname
        out.append({'off': ins.offset, 'op': ins.opname, 'arg': arg, 'argval': short(av)})
    return out


def opseq(seq):
    return [item['op'] for item in seq]


def diff_lists(a, b):
    """index-wise diff of two equal-purpose lists."""
    rows = []
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else '<missing>'
        y = b[i] if i < len(b) else '<missing>'
        if x != y:
            rows.append({'i': i, 'orig': x, 'prod': y})
    return rows


def walk(orig, prod, path, out, depth=0):
    """Compare a pair of code objects at `path`, recursing into nested code."""
    node = {'path': path, 'qualname_o': orig.co_qualname, 'qualname_p': prod.co_qualname,
            'depth': depth, 'diffs': [], 'n_consts_o': len(orig.co_consts),
            'n_consts_p': len(prod.co_consts)}
    out.append(node)

    # ---- scalar / bytes fields ----
    for field in ('co_code', 'co_exceptiontable', 'co_names', 'co_varnames',
                  'co_cellvars', 'co_freevars', 'co_stacksize', 'co_flags',
                  'co_nlocals', 'co_argcount', 'co_posonlyargcount',
                  'co_kwonlyargcount', 'co_qualname'):
        a = getattr(orig, field)
        b = getattr(prod, field)
        if isinstance(a, bytes):
            if a != b:
                node['diffs'].append({'field': field, 'kind': 'bytes',
                                      'len_o': len(a), 'len_p': len(b),
                                      'sha_o': hashlib.sha256(a).hexdigest()[:12],
                                      'sha_p': hashlib.sha256(b).hexdigest()[:12]})
        elif a != b:
            node['diffs'].append({'field': field, 'kind': 'value', 'orig': a, 'prod': b,
                                  'rows': diff_lists(list(a) if isinstance(a, (tuple, list)) else [a],
                                                     list(b) if isinstance(b, (tuple, list)) else [b])})

    # ---- co_consts: structure, order, identity ----
    ko = [const_key(v) for v in orig.co_consts]
    kp = [const_key(v) for v in prod.co_consts]
    node['consts_o'] = [const_sig(v) for v in orig.co_consts]
    node['consts_p'] = [const_sig(v) for v in prod.co_consts]
    node['consts_multiset_equal'] = collections.Counter(map(str, ko)) == collections.Counter(map(str, kp))
    node['consts_order_equal'] = ko == kp
    # for every orig constant, where does an equal-valued one sit in prod?
    perm = []
    for i, v in enumerate(orig.co_consts):
        hits = [j for j, w in enumerate(prod.co_consts) if const_key(w) == const_key(v)]
        if not hits:  # try value-equality (0 == False)
            hits = [j for j, w in enumerate(prod.co_consts)
                    if not isinstance(w, types.CodeType) and not isinstance(v, types.CodeType)
                    and w == v and type(w) is not type(v)]
            perm.append({'i': i, 'orig': short(v), 'prod_same_value_other_type': hits})
        elif hits != [i]:
            perm.append({'i': i, 'orig': short(v), 'prod_index': hits})
    if perm:
        node['const_permutation'] = perm
    if len(orig.co_consts) != len(prod.co_consts):
        node['diffs'].append({'field': 'co_consts.len', 'kind': 'len',
                              'orig': len(orig.co_consts), 'prod': len(prod.co_consts)})
    per_index = []
    for i in range(min(len(orig.co_consts), len(prod.co_consts))):
        a, b = orig.co_consts[i], prod.co_consts[i]
        if isinstance(a, types.CodeType) and isinstance(b, types.CodeType):
            walk(a, b, '%s.co_consts.v[%d]' % (path, i), out, depth + 1)
            continue
        ka, kb = const_key(a), const_key(b)
        if ka == kb:
            continue
        item = {'field': 'co_consts.v[%d]' % i, 'kind': 'const',
                'orig': const_sig(a), 'prod': const_sig(b),
                'same_type': type(a) is type(b),
                'equal_value': (not isinstance(a, types.CodeType) and not isinstance(b, types.CodeType)
                                and a == b)}
        if item['equal_value'] and not item['same_type']:
            item['verdict'] = 'T2_same_value_other_type'
        elif item['same_type'] and not item['equal_value']:
            item['verdict'] = 'T_value_differs'
        else:
            item['verdict'] = 'T_type_and_value_differ'
        per_index.append(item)
        node['diffs'].append(item)
    node['const_index_diffs'] = per_index

    # ---- instruction level ----
    if orig.co_code != prod.co_code:
        io_, ip = instrs(orig), instrs(prod)
        so, sp = opseq(io_), opseq(ip)
        node['code_diff'] = {
            'n_instr_o': len(io_), 'n_instr_p': len(ip),
            'opseq_equal': so == sp,
            'instr_o': io_, 'instr_p': ip,
        }
    return out


def classify_pair(orig, prod):
    out = []
    walk(orig, prod, '$.metadata.code', out)
    nodes = [n for n in out if n['diffs']]
    tags = set()
    for n in nodes:
        for d in n['diffs']:
            f = d['field']
            if f == 'co_code':
                cd = n.get('code_diff') or {}
                if cd.get('opseq_equal'):
                    # only operands (constant indices / jump targets) moved
                    tags.add('code_operands_only')
                else:
                    tags.add('code_opseq_differs')
            elif f.startswith('co_consts'):
                if d.get('verdict') == 'T2_same_value_other_type':
                    tags.add('T2_const_object')
                elif f == 'co_consts.len':
                    tags.add('const_len_differs')
                elif d.get('verdict') in ('T_value_differs', 'T_type_and_value_differ'):
                    tags.add('const_value_differs')
            elif f in ('co_names', 'co_varnames', 'co_cellvars', 'co_freevars'):
                tags.add('name_table_differs')
            elif f == 'co_exceptiontable':
                tags.add('exceptiontable_differs')
    return out, tags


def main():
    ev = {r['entry_id']: r for r in json.load(open(EV, encoding='utf-8'))['records']}
    tr = json.load(open(TR, encoding='utf-8'))
    entries = tr['entries']

    # group by (pyc, product content) — the same repro yields the same pair
    groups = collections.OrderedDict()
    per_entry = []
    for e in entries:
        rec = ev[e['id']]
        pyc = os.path.normpath(os.path.join(ROOT, rec['c2']['pyc_path']))
        prod = os.path.normpath(os.path.join(ROOT, rec['c3']['product_path']))
        prod_sha = hashlib.sha256(open(prod, 'rb').read()).hexdigest()
        key = (pyc, prod_sha)
        groups.setdefault(key, []).append((e, rec, prod))
        per_entry.append({'n': e['n'], 'id': e['id'], 'form': e['form'],
                          'host': e['host'], 'depth': e['depth'],
                          'source': rec['c1']['path'], 'pyc': rec['c2']['pyc_path'],
                          'product': rec['c3']['product_path'], 'product_sha256': prod_sha,
                          'judge_diff_paths': e['diff_paths'], 'group_key': prod_sha[:12]})

    payload = {'groups': [], 'entries': per_entry}
    log = io.StringIO()

    index = 0
    for (pyc, prod_sha), items in groups.items():
        index += 1
        prod = items[0][2]
        orig = load_pyc_code(pyc)
        pr = load_src_code(prod)
        nodes, tags = classify_pair(orig, pr)
        gid = '%s#%d' % (os.path.basename(pyc), index)
        g = {'group': gid, 'pyc': pyc, 'product': prod, 'product_sha256': prod_sha,
             'n_entries': len(items), 'ids': [e['id'] for e, _r, _p in items],
             'source': items[0][1]['c1']['path'], 'tags': sorted(tags), 'nodes': nodes}
        payload['groups'].append(g)

        log.write('=' * 100 + '\n')
        log.write('GROUP %s  entries=%d  source=%s\n' % (gid, len(items), g['source']))
        log.write('  pyc     = %s\n  product = %s\n  sha256(prod) = %s\n'
                  % (pyc, prod, prod_sha))
        log.write('  ids     = %s\n' % ', '.join(g['ids']))
        log.write('  tags    = %s\n' % ', '.join(sorted(tags)))
        for n in nodes:
            if not n['diffs']:
                continue
            log.write('\n  -- code object %s  (qualname %s, depth %d)\n'
                      % (n['path'], n['qualname_o'], n['depth']))
            log.write('     consts: %d vs %d  multiset_equal=%s order_equal=%s\n'
                      % (n['n_consts_o'], n['n_consts_p'], n['consts_multiset_equal'],
                         n['consts_order_equal']))
            for d in n['diffs']:
                if d['field'] == 'co_code':
                    cd = n['code_diff']
                    log.write('     co_code: %d vs %d bytes, instrs %d vs %d, opseq_equal=%s\n'
                              % (d['len_o'], d['len_p'], cd['n_instr_o'], cd['n_instr_p'],
                                 cd['opseq_equal']))
                    for a, b in zip(cd['instr_o'], cd['instr_p']):
                        if (a['op'], a['arg']) != (b['op'], b['arg']):
                            log.write('        @%-4d orig %-26s %-14s | prod %-26s %s\n'
                                      % (a['off'], a['op'] + ' ' + str(a['arg']),
                                         a['argval'], b['op'] + ' ' + str(b['arg']), b['argval']))
                elif d['field'].startswith('co_consts.v'):
                    log.write('     %s: orig=%s | prod=%s -> %s\n'
                              % (d['field'], json.dumps(d['orig'], ensure_ascii=False),
                                 json.dumps(d['prod'], ensure_ascii=False),
                                 d.get('verdict')))
                elif d['field'] == 'co_consts.len':
                    log.write('     co_consts.len: %s -> %s\n' % (d['orig'], d['prod']))
                else:
                    log.write('     %s: %s\n' % (d['field'],
                              json.dumps({k: v for k, v in d.items() if k != 'field'},
                                         ensure_ascii=False)))
            if n.get('const_permutation'):
                log.write('     const permutation: %s\n'
                          % json.dumps(n['const_permutation'], ensure_ascii=False))
            log.write('     ORIG consts: %s\n'
                      % [(i, s['t'], s.get('repr', s.get('qualname')))
                         for i, s in enumerate(n['consts_o'])])
            log.write('     PROD consts: %s\n'
                      % [(i, s['t'], s.get('repr', s.get('qualname')))
                         for i, s in enumerate(n['consts_p'])])
        log.write('\n')

    with open(OUT_JSON, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    with open(OUT_LOG, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(log.getvalue())
    print('groups=%d entries=%d' % (len(payload['groups']), len(per_entry)))
    for g in payload['groups']:
        print('  %-28s entries=%-3d tags=%s' % (g['group'], g['n_entries'], g['tags']))
    print('wrote', OUT_JSON)
    print('wrote', OUT_LOG)


if __name__ == '__main__':
    main()
