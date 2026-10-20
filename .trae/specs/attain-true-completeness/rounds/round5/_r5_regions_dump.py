# -*- coding: utf-8 -*-
"""R5 region dump: patch MatchRegion.__init__ to log every MatchRegion created.

用法: python -X utf8 _r5_regions_dump.py <pyc> <out_txt>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

pyc, out_path = sys.argv[1], sys.argv[2]
out = open(out_path, 'w', encoding='utf-8')


def log(m):
    out.write(m + '\n')
    out.flush()


from core.cfg.region_analyzer import MatchRegion  # noqa: E402


def offs(bs):
    return [getattr(b, 'start_offset', None) for b in (bs or [])]


_orig_init = MatchRegion.__init__


def patched_init(self, *a, **k):
    _orig_init(self, *a, **k)
    try:
        log('MR entry=%s case_blocks=%s' % (
            getattr(self.entry, 'start_offset', None), offs(getattr(self, 'case_blocks', None))))
        log('   patterns=%r' % (getattr(self, 'case_patterns', None),))
        log('   guards=%r' % (getattr(self, 'case_guards', None),))
        log('   bodies=%s' % [offs(b) for b in (getattr(self, 'case_bodies', None) or [])])
        log('   merge=%s blocks=%s' % (getattr(getattr(self, 'merge_block', None), 'start_offset', None),
                                       offs(getattr(self, 'blocks', None))))
    except Exception as e:
        log('   <dump error %r>' % (e,))


MatchRegion.__init__ = patched_init

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(pyc)
with open(os.path.join(HERE, '_r5_regions_dump_ok.py'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
log('=== DONE ===')
out.close()
