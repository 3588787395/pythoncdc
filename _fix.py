#!/usr/bin/env python3
with open('core/cfg/region_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '        """\n        """\n        body_set = loop_body | {header}'
new = '        """\n        body_set = loop_body | {header}'

if old in content:
    content = content.replace(old, new, 1)
    with open('core/cfg/region_analyzer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed duplicate triple-quote')
else:
    print('Pattern not found - already fixed or different')
