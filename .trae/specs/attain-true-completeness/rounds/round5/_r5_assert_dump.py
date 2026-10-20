# -*- coding: utf-8 -*-
"""R5 assert-region dump: log AssertRegion creation, then decompile.

用法: python -X utf8 _r5_assert_dump.py <pyc> <out_txt>
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


from core.cfg.region_analyzer import AssertRegion, MatchRegion  # noqa: E402


def offs(bs):
    return [getattr(b, 'start_offset', None) for b in (bs or [])]


_orig_ainit = AssertRegion.__init__


def patched_ainit(self, *a, **k):
    _orig_ainit(self, *a, **k)
    try:
        log('AR entry=%s blocks=%s' % (
            getattr(self.entry, 'start_offset', None), offs(getattr(self, 'blocks', None))))
        log('   cond=%s msg=%s parent=%s' % (
            getattr(getattr(self, 'condition_block', None), 'start_offset', None),
            getattr(getattr(self, 'message_block', None), 'start_offset', None),
            getattr(getattr(self, 'parent', None), 'region_type', None)))
    except Exception as e:
        log('   <dump error %r>' % (e,))


AssertRegion.__init__ = patched_ainit

_orig_minit = MatchRegion.__init__


def patched_minit(self, *a, **k):
    _orig_minit(self, *a, **k)
    try:
        log('MR entry=%s case_blocks=%s' % (
            getattr(self.entry, 'start_offset', None), offs(getattr(self, 'case_blocks', None))))
        log('   bodies=%s merge=%s blocks=%s' % (
            [offs(b) for b in (getattr(self, 'case_bodies', None) or [])],
            getattr(getattr(self, 'merge_block', None), 'start_offset', None),
            offs(getattr(self, 'blocks', None))))
    except Exception as e:
        log('   <dump error %r>' % (e,))


MatchRegion.__init__ = patched_minit

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(pyc)
log('=== DECOMPILED ===')
log(src)
out.close()
print('written', out_path)
