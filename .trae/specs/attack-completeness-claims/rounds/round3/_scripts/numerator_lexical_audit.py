# -*- coding: utf-8 -*-
"""numerator_lexical_audit.py — L1 口径层：分子（97/97、31/31）是否只是「源码里出现过该词」

tools/kb/syntax_coverage.py 的分子判定是纯文本判定：
  - ast 节点：正则 `\\bast\\.([A-Z]\\w+)` 扫源码全文（tools/kb/syntax_coverage.py:113-120）
  - 扩展形态：`any(hint in all_text)` 子串包含（tools/kb/syntax_coverage.py:146-184）
两者都把 **注释 / 文档字符串 / 字符串字面量** 当作「程序能产出该节点」的证据。

本脚本：
  1) 复算原口径分子（应得 97/97 与 31/31）；
  2) 构造「仅代码」文本（用 tokenize 丢弃 COMMENT 与 STRING token）后重算分子；
  3) 报告每一条因注释/字符串而虚增的节点与形态；
  4) 顺带审计 31 扩展形态与 97 节点分母的重复计数（分母非互斥分区）。
"""
import ast as pyast
import io
import json
import os
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = ROOT / '.trae/specs' / 'attack-completeness-claims' / 'rounds' / 'round3' / '_out'
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / 'tools' / 'kb'))
import syntax_coverage as sc  # noqa: E402


def code_only_text(path: Path, keep_strings: bool = False) -> str:
    """返回只含「代码」的原文本：把 COMMENT（keep_strings=False 时还包括 STRING）
    token 所在区域逐字符替换为空格，保留其它字符与偏移不变。"""
    try:
        raw = path.read_bytes()
    except OSError:
        return ''
    try:
        text = raw.decode('utf-8', 'replace')
    except Exception:
        return ''
    lines = text.splitlines(keepends=True)
    try:
        toks = list(tokenize.tokenize(io.BytesIO(raw).readline))
    except Exception:
        return text
    starts = []
    off = 0
    for ln in lines:
        starts.append(off)
        off += len(ln)
    buf = list(text)
    drop = (tokenize.COMMENT,) if keep_strings else (tokenize.COMMENT, tokenize.STRING)
    for t in toks:
        if t.type not in drop:
            continue
        srow, scol = t.start
        erow, ecol = t.end
        if srow - 1 >= len(starts):
            continue
        s = starts[srow - 1] + scol
        if erow - 1 >= len(starts):
            e = len(text)
        else:
            e = starts[erow - 1] + ecol
        for i in range(s, min(e, len(buf))):
            if buf[i] != '\n':
                buf[i] = ' '
    return ''.join(buf)


def main():
    rep = {}
    files = sc.collect_files()
    rep['source_files_scanned'] = len(files)

    denom, _, _, _ = (None, None, None, None)
    # 复算分母（与 denominator_audit.py 同规则）
    SKIP = {'AST', 'mod', 'stmt', 'expr', 'expr_context', 'boolop', 'operator',
            'unaryop', 'cmpop', 'type_ignore', 'pattern', 'typevar',
            'type_param', 'slice'}
    DEPRECATED = {'Num', 'Str', 'Bytes', 'NameConstant', 'Ellipsis',
                  'AugLoad', 'AugStore', 'Param', 'ExtSlice'}
    NON_SYNTAX = {'Interactive', 'Expression', 'FunctionType', 'Suite', 'TypeIgnore'}
    STMT_SET = {
        'FunctionDef', 'AsyncFunctionDef', 'ClassDef', 'Return', 'Delete', 'Assign',
        'AugAssign', 'AnnAssign', 'For', 'AsyncFor', 'While', 'If', 'With',
        'AsyncWith', 'Match', 'Raise', 'Try', 'TryStar', 'Assert', 'Import',
        'ImportFrom', 'Global', 'Nonlocal', 'Expr', 'Pass', 'Break', 'Continue'}
    nodes = [n for n in sorted(n for n in dir(pyast) if n[0].isupper()
                               and isinstance(getattr(pyast, n), type)
                               and issubclass(getattr(pyast, n), pyast.AST))
             if n not in DEPRECATED and n not in NON_SYNTAX]
    stmt = sorted({n for n in nodes if n.endswith('Stmt') or n in STMT_SET})
    expr = sorted(set(nodes) - set(stmt) - SKIP)
    mod = sorted(n for n in nodes if n.endswith(('Module', 'Interactive',
                                                 'Expression', 'FunctionType')))
    denominator_ast = sorted(set(stmt) | set(expr) | set(mod))
    rep['denominator_ast_size'] = len(denominator_ast)

    def ast_refs(texts, quoted_ok=True):
        refs = set()
        for txt in texts:
            for m in re.finditer(r'\bast\.([A-Z]\w+)', txt):
                refs.add(m.group(1))
            if quoted_ok:
                for m in re.finditer(r"['\"]([A-Z]\w+)['\"]", txt):
                    if m.group(1) in denominator_ast or m.group(1).startswith('Match'):
                        refs.add(m.group(1))
        return refs

    raw_texts = [p.read_text(encoding='utf-8', errors='replace') for p in files]
    code_texts = [code_only_text(p) for p in files]                 # 去注释 + 去字符串
    code_str_texts = [code_only_text(p, keep_strings=True) for p in files]  # 仅去注释（保留字符串字面量）

    # --- ast 节点分子 ---
    raw_refs = ast_refs(raw_texts, quoted_ok=True)
    code_refs = ast_refs(code_texts, quoted_ok=True)
    code_refs_strict = ast_refs(code_texts, quoted_ok=False)
    # 三层证据分级（保留字符串字面量 = 实现的节点词汇可以是 "type": "MatchAs" 形态）
    raw_cov = sorted(n for n in denominator_ast if n in raw_refs)
    code_cov = sorted(n for n in denominator_ast if n in code_refs)
    strict_cov = sorted(n for n in denominator_ast if n in code_refs_strict)
    tier = {}
    for n in denominator_ast:
        has_ast = bool(re.search(r'\bast\.' + re.escape(n) + r'\b', ''.join(code_str_texts)))
        has_q = bool(re.search(r"['\"]" + re.escape(n) + r"['\"]", ''.join(code_str_texts)))
        if has_ast:
            tier[n] = 'T1-ast.X 代码引用'
        elif has_q:
            tier[n] = 'T2-字符串字面量类型标签'
        else:
            tier[n] = 'T3-仅注释/文档字符串提及'
    rep['tier_counts'] = {
        'T1_astX_code': sum(1 for v in tier.values() if v.startswith('T1')),
        'T2_quoted_string': sum(1 for v in tier.values() if v.startswith('T2')),
        'T3_comment_only': sum(1 for v in tier.values() if v.startswith('T3')),
    }
    rep['tier_T3_nodes'] = sorted(n for n, v in tier.items() if v.startswith('T3'))
    rep['tier_map'] = tier
    rep['ast_numerator_raw'] = len(raw_cov)
    rep['ast_numerator_code_only'] = len(code_cov)
    rep['ast_numerator_code_only_strict'] = len(strict_cov)
    rep['ast_only_via_comment_or_string'] = sorted(set(raw_cov) - set(code_cov))
    rep['ast_only_via_quoted_literal'] = sorted(set(code_cov) - set(strict_cov))
    rep['ast_never_referenced'] = sorted(set(denominator_ast) - set(raw_cov))

    # --- 扩展形态分子 ---
    hints = {
        'elif_chain': ['elif', 'elif_conditions', 'IfRegion'],
        'for_else': ['else_body', 'LOOP_ELSE'],
        'multi_target_assign': ['ASTStore', 'Tuple'],
        'multi_context_with': ['should_merge_with', 'items'],
        'augmented_assign': ['AugAssign', 'BINARY_OP', 'INPLACE'],
        'walrus': ['NamedExpr', 'COPY'],
        'decorator_with_args': ['Decorator', 'decorator'],
        'keyword_args': ['keywords', 'KW_NAMES'],
        'star_args': ['Starred', 'CALL_FUNCTION_EX', 'UNPACK'],
        'chained_comparison': ['CHAINED_COMPARE', 'Compare'],
        'star_import': ['ImportFrom', 'import_all', 'level'],
        'relative_import': ['level', 'ImportFrom'],
        'global_nonlocal': ['Global', 'Nonlocal', 'STORE_GLOBAL'],
        'slice': ['Slice', 'BUILD_SLICE', 'slice'],
        'fstring_conversion': ['FormattedValue', 'conversion', 'format_spec'],
        'async_def': ['AsyncFunctionDef', 'async'],
        'async_for': ['AsyncFor', 'GET_AITER', 'GET_ANEXT'],
        'async_with': ['AsyncWith', 'BEFORE_ASYNC_WITH'],
        'await_expr': ['Await', 'GET_AWAITABLE', 'SEND'],
        'yield_from': ['YieldFrom', 'GET_YIELD_FROM_ITER', 'is_yield_from_loop'],
        'nested_comprehension': ['multi_for', 'comprehension', 'for_iter_indices'],
        'try_finally_only': ['finally', 'finalbody', 'has_finally'],
        'except_star': ['is_except_star', 'PREP_RERAISE_STAR'],
        'match_statement': ['Match', 'MATCH_', 'MatchRegion'],
        'case_guard': ['guard', 'MatchCase'],
        'class_keyword_pattern': ['MatchClass', 'MatchClass'],
        'mapping_pattern': ['MatchMapping', 'MatchMapping'],
        'sequence_pattern': ['MatchSequence', 'MatchSequence'],
        'or_pattern': ['MatchOr', 'MatchOr'],
        'capture_pattern': ['MatchAs', 'MatchStar'],
        'value_pattern': ['MatchValue', 'MatchValue', 'MatchSingleton'],
    }
    all_raw = ''.join(raw_texts)
    all_code = ''.join(code_texts)
    all_code_str = ''.join(code_str_texts)
    extra_raw, extra_code, extra_code_str = [], [], []
    detail = {}
    for k, hs in hints.items():
        hit_raw = [h for h in hs if h in all_raw]
        hit_code = [h for h in hs if h in all_code]
        hit_code_str = [h for h in hs if h in all_code_str]
        if hit_raw:
            extra_raw.append(k)
        if hit_code:
            extra_code.append(k)
        if hit_code_str:
            extra_code_str.append(k)
        detail[k] = {'hint': hs, 'hit_raw': hit_raw, 'hit_code': hit_code,
                     'hit_code_keepstrings': hit_code_str}
    rep['extra_forms_raw_count'] = len(extra_raw)
    rep['extra_forms_code_only_count'] = len(extra_code)
    rep['extra_forms_code_keepstrings_count'] = len(extra_code_str)
    rep['extra_forms_only_via_comment_or_string'] = sorted(set(extra_raw) - set(extra_code))
    rep['extra_forms_comment_only_evidence'] = sorted(set(extra_raw) - set(extra_code_str))
    rep['extra_forms_detail'] = detail

    # --- 31 扩展形态 与 97 节点分母 的重复计数审计 ---
    dropped_lower = {'alias', 'arg', 'arguments', 'comprehension', 'keyword',
                     'match_case', 'withitem'}
    dup = {}
    for k, desc in sc.EXTRA_FORMS.items():
        refs = re.findall(r'ast\.([A-Za-z_]\w+)', desc)
        refs += re.findall(r'\b([A-Z][A-Za-z_]*)\b', desc)
        refs = sorted({r for r in refs if r in denominator_ast})
        dup[k] = refs
    # 语义目标（含小写被丢弃类）
    sem = {
        'except_star': ['TryStar'], 'star_import': ['alias'],
        'nested_comprehension': ['comprehension'], 'case_guard': ['match_case'],
        'keyword_args': ['Call', 'keyword'], 'multi_context_with': ['With', 'withitem'],
        'multi_target_assign': ['Tuple'], 'capture_pattern': ['MatchAs', 'MatchStar'],
        'value_pattern': ['MatchValue', 'MatchSingleton'],
        'global_nonlocal': ['Global', 'Nonlocal'],
    }
    for k in sc.EXTRA_FORMS:
        if k not in sem:
            refs = re.findall(r'ast\.([A-Za-z_]\w+)', sc.EXTRA_FORMS[k])
            refs += re.findall(r'\b([A-Z][A-Za-z_]*)\b', sc.EXTRA_FORMS[k])
            sem[k] = sorted({r for r in refs if r in denominator_ast or r in dropped_lower})
    cls = {}
    for k in sc.EXTRA_FORMS:
        targets = sem.get(k, [])
        if any(t in denominator_ast for t in targets):
            cls[k] = 'overlaps_node_in_97'
        elif any(t in dropped_lower for t in targets):
            cls[k] = 'compensates_dropped_lowercase_class'
        else:
            cls[k] = 'new_language_surface'
    rep['extra_forms_classification'] = cls
    rep['extra_forms_class_counts'] = {
        'overlaps_node_in_97': sum(1 for v in cls.values() if v == 'overlaps_node_in_97'),
        'compensates_dropped_lowercase_class': sum(
            1 for v in cls.values() if v == 'compensates_dropped_lowercase_class'),
        'new_language_surface': sum(1 for v in cls.values() if v == 'new_language_surface'),
    }
    rep['extra_forms_mapped_to_denominator_nodes'] = dup
    rep['extra_forms_fully_covered_by_denominator'] = sorted(
        k for k, v in dup.items() if v)
    rep['extra_forms_count_with_denominator_overlap'] = sum(1 for v in dup.values() if v)

    out = OUT / 'numerator_lexical_audit.json'
    io.open(out, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(rep, ensure_ascii=False, indent=2))

    print('扫描源码文件数      :', len(files))
    print('分母 ast 节点数     :', len(denominator_ast))
    print('分子(原口径,含注释/字符串):', len(raw_cov), '/', len(denominator_ast))
    print('分子(去注释+去字符串)  :', len(code_cov), '/', len(denominator_ast))
    print('分子(仅去注释,留字面量):', len(code_cov), '/', len(denominator_ast))
    print('分子(仅 ast.X 代码引用):', len(strict_cov), '/', len(denominator_ast))
    print('证据分级 T1/T2/T3      :', rep['tier_counts'])
    print('T3 仅注释/文档字符串提及:', len(rep['tier_T3_nodes']), rep['tier_T3_nodes'][:20])
    print('仅靠注释/字符串命中    :', len(rep['ast_only_via_comment_or_string']))
    print('仅靠裸引号字面量命中   :', len(rep['ast_only_via_quoted_literal']))
    print('从未被引用             :', rep['ast_never_referenced'])
    print()
    print('扩展形态分子(原口径)   :', len(extra_raw), '/', len(hints))
    print('扩展形态(去注释+去字符串):', len(extra_code), '/', len(hints))
    print('扩展形态(仅去注释)     :', len(extra_code_str), '/', len(hints))
    print('仅靠注释/字符串命中    :', rep['extra_forms_only_via_comment_or_string'])
    print('仅靠注释命中(留字面量)  :', rep['extra_forms_comment_only_evidence'])
    print()
    print('31 扩展形态中已有对应 ast 节点分母项的个数:',
          rep['extra_forms_count_with_denominator_overlap'], '/', len(hints))
    print('31 形态三分归类:', rep['extra_forms_class_counts'])
    for k, v in sorted(cls.items()):
        if v != 'overlaps_node_in_97':
            print('   %-22s %-38s -> %s' % (k, v, sem.get(k)))
    for k, v in sorted(dup.items()):
        if v:
            print('   %-22s -> %s' % (k, v))
    print('JSON ->', out)


if __name__ == '__main__':
    main()
