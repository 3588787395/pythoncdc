"""Byte-level probe builder for r74: add stderr-only probes around the orphan-release path of
core/cfg/region_ast_generator.py so we can see whether block @6778 (merge of IfRegion@6690) is
released as an orphan and where its BASIC region lands in the emission order.

Probe writes only to stderr when env R74_PROBE is set; it never feeds back into any decision, so
the product must be byte-identical with and without it (verified separately).

usage: python -X utf8 work/probe_orphan.py --out work/PROBED.py
"""
import hashlib
import py_compile
import sys

SRC = 'D:/Temp/r74/core/cfg/region_ast_generator.py'
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'D:/Temp/r74/work/PROBED.py'
b = open(SRC, 'rb').read()
lines = b.split(b'\r\n')


def anchor_count(sub):
    return sum(1 for l in lines if sub in l)


a1 = b'                    _orphaned_blocks.append(_block)'
a2 = b'                self.regions.append(_basic_region)'
assert anchor_count(a1) == 1, anchor_count(a1)
assert anchor_count(a2) == 1, anchor_count(a2)

p1 = (b'                    import os as _o\n'
      b'                    if _o.environ.get("R74_PROBE"):\n'
      b'                        import sys as _s\n'
      b'                        _s.stderr.write("R74ORPHAN %s region=%s parent=%s\\n" % (\n'
      b'                            _block.start_offset, type(_region).__name__,\n'
      b'                            getattr(_region, "parent", None) and _region.parent.start_offset))')
p2 = (b'                import os as _o2\n'
      b'                if _o2.environ.get("R74_PROBE"):\n'
      b'                    import sys as _s2\n'
      b'                    _s2.stderr.write("R74BASIC %s idx=%s\\n" % (_blk.start_offset, len(top_level_regions) - 1))')

for anchor, probe in ((a1, p1), (a2, p2)):
    i = lines.index(anchor)
    lines[i] = probe + b'\r\n' + lines[i]

# dump final emission order of top-level region entries right after the region list is settled
a3 = b'        _exc_cleanup_opnames = frozenset({'
assert anchor_count(a3) == 1
i = lines.index(a3)
p3 = (b'        import os as _o3\r\n'
      b'        if _o3.environ.get("R74_PROBE"):\r\n'
      b'            import sys as _s3\r\n'
      b'            _s3.stderr.write("R74ORDER %s\\n" % str([getattr(_r.entry, "start_offset", None) for _r in top_level_regions]))')
lines[i] = p3 + b'\r\n' + lines[i]

out = b'\r\n'.join(lines)
open(OUT, 'wb').write(out)
py_compile.compile(OUT, doraise=True)
print('probe build=%s size=%d sha16=%s' % (OUT, len(out), hashlib.sha256(out).hexdigest()[:16]))
