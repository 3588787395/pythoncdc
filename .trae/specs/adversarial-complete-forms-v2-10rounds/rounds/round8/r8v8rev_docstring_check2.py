# -*- coding: utf-8 -*-
"""I.7 check: touched mandatory-class (_identify_* / _generate_*) methods keep
six-item docstrings; plus B108 docstring declaration spots."""
import io
import sys
sys.stdout.reconfigure(encoding='utf-8')


def docstring_of(path, marker):
    ls = io.open(path, encoding='utf-8', errors='replace').read().splitlines()
    for i, l in enumerate(ls):
        if marker in l:
            buf = []
            started = False
            for j in range(i, min(i + 320, len(ls))):
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
checks = [
    ('core/cfg/region_analyzer.py', 'def _identify_loop_regions', 'loop_ident'),
    ('core/cfg/region_analyzer.py', 'def _identify_conditional_regions', 'cond_ident'),
    ('core/cfg/region_analyzer.py', 'def _identify_boolop_regions', 'boolop_ident'),
    ('core/cfg/region_analyzer.py', 'def _identify_chained_compare_regions', 'ccmp_ident'),
    ('core/cfg/region_analyzer.py', 'def _identify_match_regions', 'match_ident'),
    ('core/cfg/region_analyzer.py', 'def _identify_try_except_regions', 'try_ident'),
    ('core/cfg/region_ast_generator.py', 'def _generate_ternary', 'gen_ternary'),
    ('core/cfg/region_ast_generator.py', 'def _generate_match', 'gen_match'),
    ('core/cfg/region_ast_generator.py', 'def _generate_with', 'gen_with'),
    ('core/cfg/region_ast_generator.py', 'def _loop_generate_while', 'gen_while'),
    ('core/cfg/region_ast_generator.py', 'def _generate_try_body', 'gen_trybody'),
    ('core/cfg/region_ast_generator.py', 'def _generate_handler_body_statements', 'gen_handler'),
]
for path, marker, tag in checks:
    ds = docstring_of(path, marker)
    if ds is None:
        print('%-12s %-42s : NO DOCSTRING' % (tag, marker))
        continue
    six = [t for kw, t in items if kw in ds]
    cs = [c for c in ('C1', 'C2', 'C3') if c in ds]
    print('%-12s %-42s : six-items %d/6 %s  C %s  len=%d'
          % (tag, marker, len(six), ''.join(six), ''.join(cs), len(ds)))
