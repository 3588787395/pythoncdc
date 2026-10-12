# -*- coding: utf-8 -*-
"""I.7 docstring structural check for round8 fix first-anchor methods."""
import io
import sys
sys.stdout.reconfigure(encoding='utf-8')


def docstring_of(path, marker):
    ls = io.open(path, encoding='utf-8', errors='replace').read().splitlines()
    for i, l in enumerate(ls):
        if marker in l:
            buf = []
            started = False
            for j in range(i, min(i + 260, len(ls))):
                t = ls[j]
                if not started and '"""' in t:
                    started = True
                    if t.count('"""') >= 2:
                        return t
                    continue
                if started:
                    if '"""' in t:
                        return '\n'.join(buf)
                    buf.append(t)
            return '\n'.join(buf)
    return None


items = [('算法依据', 'Y1'), ('归约顺序', 'Y2'), ('唯一归属', 'Y3'),
         ('嵌套', 'Y4'), ('入口引用', 'Y5'), ('反编译流程', 'Y6')]
methods = [
    ('core/cfg/region_analyzer.py', 'def _cleanup_try_else_in_loop_body', 'B109'),
    ('core/cfg/region_ast_generator.py', 'def _try_build_orprefix_and_boolop_from_ternary', 'B98R1'),
    ('core/cfg/region_ast_generator.py', 'def _try_build_match_case_ternary_stmt', 'B77'),
    ('core/cfg/region_ast_generator.py', 'def _build_chained_complex_target_assign', 'B107'),
    ('core/cfg/pattern_parser.py', 'def _extract_case_guard_from_blocks', 'B81'),
    ('core/cfg/pattern_parser.py', 'def _collect_or_arm_chain_instrs', 'B103G2'),
    ('core/cfg/pattern_parser.py', 'def _pure_jf_argval', 'B103G2b'),
    ('core/cfg/region_analyzer.py', 'def _b102_degenerate_chain_pairs_finally', 'B102E2'),
    ('core/cfg/region_analyzer.py', 'def _b102_chain_reachable_blocks', 'B102E2b'),
    ('core/cfg/region_analyzer.py', 'def _find_star_else_blocks', 'B102E4'),
    ('core/cfg/comprehension_generator.py', 'def _b113_extract_flat_clauses', 'B113C1'),
]
for path, marker, fam in methods:
    ds = docstring_of(path, marker)
    if ds is None:
        print('%-8s %-50s : DOCSTRING NOT FOUND' % (fam, marker))
        continue
    six = [tag for kw, tag in items if kw in ds]
    cs = [c for c in ('C1', 'C2', 'C3') if c in ds]
    print('%-8s %-50s : six-items %d/6 %s  C-clauses %s'
          % (fam, marker, len(six), ''.join(six), ''.join(cs)))
