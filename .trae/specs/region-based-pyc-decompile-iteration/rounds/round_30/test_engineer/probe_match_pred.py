"""实测某个块被哪些 match 判据命中（定位伪 MatchRegion 来源）。

用法: D:/Python/python.exe probe_match_pred.py <pyc路径> <块起始offset>
"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_analyzer import RegionAnalyzer

_state = {'offset': None, 'done': False, 'sig': None}

_preds = ('_has_match_op', '_is_match_subject_block',
          '_is_simple_match_case_block', '_is_wildcard_match_block',
          '_is_none_match_block', '_is_except_star_framework_block',
          '_is_case_pattern_block', '_is_literal_default_block')

_orig_analyze = RegionAnalyzer.analyze


def patched_analyze(self, *a, **kw):
    res = _orig_analyze(self, *a, **kw)
    if _state['done']:
        return res
    blk = self.cfg.get_block_by_offset(_state['offset'])
    sig = _state['sig']
    if blk is not None and sig:
        sigs = {(i.offset, i.opname) for i in blk.instructions}
        if not sig.issubset(sigs):
            return res
    if blk is None:
        return res
    _state['done'] = True
    print('=== block @%s  (%d instr) ===' % (_state['offset'],
                                             len(blk.instructions)))
    for i in blk.instructions:
        print('   %4d %s' % (i.offset, i.opname + (' ' + str(i.argval)
                                                   if i.arg is not None else '')))
    for name in _preds:
        fn = getattr(self, name, None)
        if fn is None:
            print('  %-38s (missing)' % name)
            continue
        try:
            v = fn(blk)
        except Exception as e:  # noqa: BLE001
            v = 'EXC %s: %s' % (type(e).__name__, e)
        print('  %-38s -> %s' % (name, v))
    print('  block_to_region ->', type(self.block_to_region.get(blk)).__name__
          if self.block_to_region.get(blk) is not None else None)
    for r in self.regions:
        if blk in (getattr(r, 'blocks', None) or []):
            print('  region %s blocks=%s' % (
                type(r).__name__,
                sorted(getattr(b, 'start_offset', -1) for b in r.blocks)))
    return res


RegionAnalyzer.analyze = patched_analyze


def main():
    from pycdc import decompile_pyc
    _state['offset'] = int(sys.argv[2])
    # 可选签名: 216=COPY,262=STORE_ATTR 形式 '216:COPY,262:STORE_ATTR'
    if len(sys.argv) > 3:
        _state['sig'] = {tuple(t.split(':')) for t in sys.argv[3].split(',')}
        _state['sig'] = {(int(a), b) for a, b in _state['sig']}
    decompile_pyc(sys.argv[1], use_cfg=True)


if __name__ == '__main__':
    main()
