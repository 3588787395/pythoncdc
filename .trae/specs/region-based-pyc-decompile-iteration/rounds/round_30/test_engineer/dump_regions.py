"""导出包含指定指令的区域结构（定位区域边界误判的通用工具）。

打桩 RegionASTGenerator._generate_region，只打印「覆盖给定 (offset, opname) 指令」
的区域，输出其类型、块偏移、以及各命名块的完整指令序列。

用法:
  D:/Python/python.exe dump_regions.py <pyc路径> <offset> [opname]
  D:/Python/python.exe dump_regions.py <pyc路径> all          # 打印全部区域概览
"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

_orig = RegionASTGenerator._generate_region
_state = {'offset': None, 'opname': None, 'n': 0, 'all': False}


def dump_region(region):
    rtype = type(region).__name__
    blocks = list(getattr(region, 'blocks', []) or [])
    offs = sorted(getattr(b, 'start_offset', -1) for b in blocks)
    print('--- %s  blocks=%s' % (rtype, offs))
    seen = set()
    for attr in ('entry', 'cond_block', 'true_block', 'false_block',
                 'value_block', 'merge_block', 'exit_block', 'body_block'):
        b = getattr(region, attr, None)
        if b is None:
            continue
        seen.add(id(b))
        ins = list(getattr(b, 'instructions', None) or [])
        if not ins:
            continue
        print('  [%s] off=%s  %d instr' % (attr, getattr(b, 'start_offset', '?'),
                                           len(ins)))
        for i in ins:
            print('      %4d %s' % (i.offset,
                                    i.opname + (' ' + str(i.argval)
                                                if i.arg is not None else '')))
    for b in blocks:
        if id(b) in seen:
            continue
        ins = list(getattr(b, 'instructions', None) or [])
        print('  [other] off=%s  %d instr' % (getattr(b, 'start_offset', '?'),
                                              len(ins)))
        for i in ins:
            print('      %4d %s' % (i.offset,
                                    i.opname + (' ' + str(i.argval)
                                                if i.arg is not None else '')))


def covers(region):
    blocks = list(getattr(region, 'blocks', []) or [])
    for b in blocks:
        for i in (getattr(b, 'instructions', None) or []):
            if getattr(i, 'offset', None) == _state['offset']:
                if _state['opname'] is None or i.opname == _state['opname']:
                    return True
    return False


def patched(self, region, *a, **kw):
    if _state['all']:
        blocks = list(getattr(region, 'blocks', []) or [])
        offs = sorted(getattr(b, 'start_offset', -1) for b in blocks)
        print('%-24s blocks=%s' % (type(region).__name__, offs))
        _state['n'] += 1
        return _orig(self, region, *a, **kw)
    if covers(region):
        _state['n'] += 1
        dump_region(region)
    return _orig(self, region, *a, **kw)


RegionASTGenerator._generate_region = patched


def main():
    from pycdc import decompile_pyc
    if sys.argv[2] == 'all':
        _state['all'] = True
    else:
        _state['offset'] = int(sys.argv[2])
        _state['opname'] = sys.argv[3] if len(sys.argv) > 3 else None
    decompile_pyc(sys.argv[1], use_cfg=True)
    print('=== dumped %d regions ===' % _state['n'])


if __name__ == '__main__':
    main()
