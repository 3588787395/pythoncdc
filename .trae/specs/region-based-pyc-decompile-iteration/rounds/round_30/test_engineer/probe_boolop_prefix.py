"""探测 BoolOpRegion 的前缀切分链路（定位前缀边界为何不对）。

打桩 _generate_boolop，导出：
  - region.prefix_block / entry 及其指令范围
  - identify_block_prefix_instructions 的返回值
  - _build_prefix_stmt_list 的返回语句

用法: D:/Python/python.exe probe_boolop_prefix.py <pyc路径> <offset> [opname]
"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

_orig_boolop = RegionASTGenerator._generate_boolop
_orig_pfx = RegionASTGenerator._build_prefix_stmt_list
_state = {'offset': None, 'opname': None, 'done': False}


def covers(region):
    for b in (getattr(region, 'blocks', None) or []):
        for i in (getattr(b, 'instructions', None) or []):
            if getattr(i, 'offset', None) == _state['offset']:
                if _state['opname'] is None or i.opname == _state['opname']:
                    return True
    return False


def show_instrs(tag, ins):
    print('  %s: %d instr  [%s]' % (
        tag, len(ins),
        ', '.join(str(getattr(i, 'offset', '?')) for i in (ins or []))))


def patched_boolop(self, region, *a, **kw):
    if _state['done'] or not covers(region):
        return _orig_boolop(self, region, *a, **kw)
    _state['done'] = True
    print('=== BoolOpRegion ===')
    print('prefix_block =', getattr(region, 'prefix_block', None))
    pb = getattr(region, 'prefix_block', None)
    for tag, b in (('prefix_block', pb), ('entry', getattr(region, 'entry', None))):
        if b is None:
            print('  %s = None' % tag)
            continue
        print('  %s off=%s' % (tag, getattr(b, 'start_offset', '?')))
        show_instrs('   instrs', list(getattr(b, 'instructions', None) or []))
    print('op_chain =', [(getattr(b, 'start_offset', '?'), op)
                         for b, op in (getattr(region, 'op_chain', None) or [])])
    print('value_target =', getattr(region, 'value_target', None))
    if pb is not None:
        pre = self.region_analyzer.identify_block_prefix_instructions(pb)
        show_instrs('identify_block_prefix_instructions', pre)
        stmts = _orig_pfx(self, pre, pb)
        print('  _build_prefix_stmt_list -> %d stmt(s)' % len(stmts))
        for s in stmts:
            print('    ', str(s)[:160])
    print('=== end ===')
    return _orig_boolop(self, region, *a, **kw)


RegionASTGenerator._generate_boolop = patched_boolop


def main():
    from pycdc import decompile_pyc
    _state['offset'] = int(sys.argv[2])
    _state['opname'] = sys.argv[3] if len(sys.argv) > 3 else None
    decompile_pyc(sys.argv[1], use_cfg=True)


if __name__ == '__main__':
    main()
