# -*- coding: utf-8 -*-
"""build a single-anchor single-file spec from the CURRENT worktree bytes (read-only)."""
import io, json, sys
REPO = r'F:/Downloads/pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')

def norm(rel):
    src = io.open(REPO + '/' + rel, encoding='utf-8-sig', newline='').read()
    nl = '\r\n' if src.count('\r') else '\n'
    return src.replace(nl, '\n'), nl

def make(rel, start_marker, end_marker, insert, out, tag):
    u, nl = norm(rel)
    i = u.index(start_marker)
    j = u.index(end_marker, i)
    anchor = u[i:j]
    assert u.count(anchor) == 1, ('anchor not unique', u.count(anchor))
    repl = anchor[:anchor.rindex('\n')] + '\n' + insert + '\n' + anchor[anchor.rindex('\n') + 1:]
    # simpler: insert BEFORE end_marker
    repl = anchor + insert
    assert u.count(anchor) == 1
    spec = {'file': rel, 'anchor': anchor, 'repl': anchor + insert}
    assert spec['repl'].count(spec['anchor']) == 1
    io.open(out, 'w', encoding='utf-8', newline='\n').write(json.dumps(spec, ensure_ascii=False, indent=1))
    print('%s -> %s  anchor_lines=%d insert_lines=%d' % (
        tag, out, anchor.count('\n'), insert.count('\n')))

if __name__ == '__main__':
    pass
