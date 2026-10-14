"""Build a PROBE-patched copy of the [R21-55c] generator half: records every `_adopt_arm`
adoption and whether the [R21-55c] exception-successor relaxation was the reason it passed.
Recording only appends to a module-level list => no behavioural change (proven inert by
comparing products with and without the probe).

usage: python -X utf8 work/build_probe_gen.py <SRC C candidate> <DST probe generator>
"""
import hashlib
import os
import sys

SRC, DST = sys.argv[1], sys.argv[2]
raw = open(SRC, 'rb').read()
print('SRC sha16 =', hashlib.sha256(raw).hexdigest()[:16], len(raw))
lines = raw.split(b'\r\n')

i = [k for k, l in enumerate(lines) if l == b"            for sb in (getattr(arm, 'successors', None) or set()):"]
assert len(i) == 1, i
i = i[0]
lines[i:i] = [b"            _r2156_relaxed = False"]

j = [k for k, l in enumerate(lines) if l == b"                    return False" and lines[k - 1] == b"                if _r2155_sb_first.opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):"]
assert len(j) == 1, j
j = j[0]
lines[j + 1:j + 1] = [b"                _r2156_relaxed = True"]

k = [m for m, l in enumerate(lines) if l == b"            visited.add(arm)" and lines[m - 1] == b"                _r2156_relaxed = True"]
assert len(k) == 1, k
k = k[0]
lines[k:k] = [
    b"            _R2156_PROBE.append({",
    b"                'cond': getattr(cond_block, 'start_offset', None),",
    b"                'arm': arm.start_offset,",
    b"                'merge': getattr(merge, 'start_offset', None),",
    b"                'relaxed': bool(_r2156_relaxed),",
    b"                'ops': [x.opname for x in ai],",
    b"                'succs': sorted(getattr(sb, 'start_offset', 0) for sb in (arm.successors or [])),",
    b"                'succ_first': [getattr(sb.get_first_instruction(), 'opname', '') for sb in (arm.successors or [])],",
    b"            })",
]

# module-level sink, before the class header (class scope is invisible to nested funcs)
m = [n for n, l in enumerate(lines) if l.startswith(b"class RegionASTGenerator")]
assert len(m) == 1, m
m = m[0]
lines[m:m] = [b"_R2156_PROBE = []", b""]

out = b'\r\n'.join(lines)
assert b'\r\r\n' not in out
os.makedirs(os.path.dirname(DST) or '.', exist_ok=True)
open(DST, 'wb').write(out)
print('DST =', DST, 'sha16 =', hashlib.sha256(out).hexdigest()[:16], len(out))
compile(out.decode('utf-8-sig'), DST, 'exec')
import py_compile
py_compile.compile(DST, doraise=True)
print('compile + py_compile OK')
