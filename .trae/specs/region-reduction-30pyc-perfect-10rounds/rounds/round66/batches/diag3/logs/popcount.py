import io, os, sys, json
BS = chr(92)
REPO = 'F:/Downloads/pythoncdc-main'
ROOT = 'D:/Temp/opencode/r66gate/diag3'
TARGETS = {
 'real_quote': REPO + '/site-packages/IQData/plugins/plugin_system_realquote/real_quote.pyc',
 'klinedata': REPO + '/site-packages/IQCommon/api/klinedata.pyc',
 'synth': ROOT + '/synth/r66d3_shared_store.pyc',
}
def norm(s): return s.replace(BS, '/')
arm = sys.argv[1]
core = REPO if arm == 'landed' else ROOT + '/mirr_' + arm
sys.path.insert(0, core); sys.path.append(REPO)
import pycdc
assert norm(os.path.dirname(os.path.abspath(pycdc.__file__))) == core
ap = core + '/core/cfg/region_analyzer.py'
lines = io.open(ap, encoding='utf-8', newline='').read().replace(chr(13) + chr(10), chr(10)).split(chr(10))
pops = [i + 1 for i, l in enumerate(lines) if 'chain.pop()' in l]
r65 = [i + 1 for i, l in enumerate(lines) if 'R65-diag4' in l or 'R64-diag1' in l]
gate = [i + 1 for i, l in enumerate(lines) if 'R66-diag3 value-context chained-compare gate' in l]
anchor = [i + 1 for i, l in enumerate(lines) if 'if not _can_be_ternary_header(block):' in l]
hits = {p: 0 for p in pops}
gstart = gate[0] + 1 if gate else -1
gcount = [0]
def local(frame, ev, arg):
    if ev == 'line':
        if frame.f_lineno in hits:
            hits[frame.f_lineno] += 1
        if frame.f_lineno == gstart:
            gcount[0] += 1
    return local
def trace(frame, ev, arg):
    if norm(frame.f_code.co_filename).endswith('cfg/region_analyzer.py'):
        return local
    return None
res = {'arm': arm, 'chain_pop_lines': pops, 'r65_r64_comment_lines': r65,
       'r66_gate_comment_line': gate, 'gate_call_line': anchor, 'files': {}}
for name, p in TARGETS.items():
    h0 = dict(hits); g0 = gcount[0]
    sys.settrace(trace)
    text = pycdc.decompile_pyc(p)
    sys.settrace(None)
    res['files'][name] = {'pop_hits': {str(k): hits[k] - h0[k] for k in hits}, 'gate_entered': gcount[0] - g0}
print(json.dumps(res, ensure_ascii=False))
