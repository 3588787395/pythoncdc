# PATCH_R21-82_region_ast_generator.py
# Idempotent absolute-path anchored edit of region_ast_generator.py.
#   base: R21-81 candidate 8da14b53a94e07c3  ->  R21-82 candidate.
# (R21-81 itself is produced from landed 566ff5c502276e48 by PATCH_R21-81_region_ast_generator.py;
#  this script builds ON TOP of the 8da14b53 bytes so the two ledger halves compose reproducibly.)
#
# Mechanism: the R21-81 emission ledger `_r2181_emitted_entries` is written only at the central
# dispatch funnel `_generate_region`.  Structural regions are also emitted by DIRECT calls to
# _generate_if/_generate_try/_generate_loop/_generate_with/_generate_match that bypass the funnel;
# those emissions are never recorded, so an ancestor arm that re-offers such an entry sees it as
# "not yet emitted" and dispatches it a second time -> double emission -> collateral regressions
# (quote 92/92->89/92, real_quote 45/45->42/45).  R21-82 records the SAME fact at every such
# emission site, POST-emission, guarded on the produced source being non-empty (never at method
# entry, which would assert an emission that may not happen).  No offsets-as-keys, no names,
# no counters/thresholds -- region data (region.entry) only, correct-at-identification.
import ast
import hashlib
import re
import subprocess
import sys

TARGET = r'D:/Temp/r109/core/cfg/region_ast_generator.py'
BASE_SHA16 = '8da14b53a94e07c3'
BOM = b'\xef\xbb\xbf'
METHODS = ('_generate_if', '_generate_try', '_generate_loop', '_generate_with', '_generate_match')
NOTE = 'self._r2181_note_emitted'

ASSIGN_RE = re.compile(r'^(\s*)([A-Za-z_]\w*)\s*=\s*self\.(%s)\((\w+)\)\s*$' % '|'.join(METHODS))
LIST_RE = re.compile(r'^(\s*)([A-Za-z_]\w*)\s*=\s*\[\s*self\.(%s)\((\w+)\)\s*\]\s*$' % '|'.join(METHODS))
RET_RE = re.compile(r'^(\s*)return self\.(%s)\((\w+)\)\s*$' % '|'.join(METHODS))


def call_sites(lines):
    """Return list of (lineno1based, kind, indent, result_or_None, region, method)."""
    src = '\n'.join(lines)
    tree = ast.parse(src)
    gr = None
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == '_generate_region':
            gr = (n.lineno, n.end_lineno)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            f = n.func
            if f.attr in METHODS and isinstance(f.value, ast.Name) and f.value.id == 'self':
                ln = n.lineno
                if gr and gr[0] <= ln <= gr[1]:
                    continue  # funnel already records these
                text = lines[ln - 1]
                m = ASSIGN_RE.match(text)
                lm = LIST_RE.match(text)
                rm = RET_RE.match(text)
                if m:
                    indent, res, _meth, reg = m.groups()
                    out.append((ln, 'assign', indent, res, reg, f.attr))
                elif lm:
                    indent, res, _meth, reg = lm.groups()
                    out.append((ln, 'list', indent, res, reg, f.attr))
                elif rm:
                    indent, _meth, reg = rm.groups()
                    out.append((ln, 'return', indent, None, reg, f.attr))
                else:
                    out.append((ln, 'SKIP', '', None, None, f.attr))
    return out


def main():
    raw = open(TARGET, 'rb').read()
    before = hashlib.sha256(raw).hexdigest()[:16]
    lines = raw.decode('utf-8-sig').split('\r\n')
    sites = call_sites(lines)
    skipped = [s for s in sites if s[1] == 'SKIP']
    for s in skipped:
        print('[R21-82] NOTE unhandled call-shape at line %d (%s) -- skipped' % (s[0], s[5]))
    # apply from highest lineno to lowest so lower indices are unaffected
    applied = []
    for ln, kind, indent, res, reg, meth in sorted(sites, key=lambda t: -t[0]):
        if kind == 'assign':
            note = indent + '%s(%s, %s)' % (NOTE, reg, res)
        elif kind == 'list':
            note = indent + '%s(%s, %s)' % (NOTE, reg, res)
        elif kind == 'return':
            note = None
        else:
            continue
        if kind == 'return':
            var = '_r2182_%s' % meth[10:]
            repl = [indent + '%s = self.%s(%s)' % (var, meth, reg),
                    indent + '%s(%s, %s)' % (NOTE, reg, var),
                    indent + 'return %s' % var]
            if lines[ln - 1].strip().startswith(NOTE):
                continue
            lines[ln - 1:ln] = repl
            applied.append('return@%d %s' % (ln, meth))
        else:
            # idempotency: the very next non-blank line is our note for this site
            nxt = lines[ln] if ln < len(lines) else ''
            if nxt.strip() == '%s(%s, %s)' % (NOTE, reg, res):
                applied.append('skip@%d(already)' % ln)
                continue
            lines[ln:ln] = [note]
            applied.append('insert@%d %s(%s<-%s)' % (ln, meth, reg, res))
    out = '\r\n'.join(lines).encode('utf-8')
    if raw.startswith(BOM):
        out = BOM + out
    assert out.count(b'\r\r\n') == 0, 'CR CR LF corruption'
    assert out.count(b'\n') - out.count(b'\r\n') == 0, 'bare LF introduced'
    assert out.startswith(BOM), 'BOM lost'
    open(TARGET, 'wb').write(out)
    assert open(TARGET, 'rb').read() == out, 'write-back mismatch'
    assert subprocess.run([sys.executable, '-X', 'utf8', '-m', 'py_compile',
                           TARGET]).returncode == 0, 'py_compile failed'
    print('[R21-82] base sha16=%s applied=%d edits' % (before, len(applied)))
    for a in applied:
        print('   ', a)
    print('[R21-82] bytes=%d sha16=%s crlf=%d bareLF=%d crCRCR=%d bom=%s' % (
        len(out), hashlib.sha256(out).hexdigest()[:16], out.count(b'\r\n'),
        out.count(b'\n') - out.count(b'\r\n'), out.count(b'\r\r\n'), out.startswith(BOM)))


main()
