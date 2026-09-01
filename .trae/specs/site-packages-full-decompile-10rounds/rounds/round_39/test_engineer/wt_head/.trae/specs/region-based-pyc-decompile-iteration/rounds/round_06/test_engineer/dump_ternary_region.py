"""打印 TernaryRegion 的结构（块范围与每块指令），定位区域边界误判。

打桩 RegionASTGenerator._generate_ternary，在入口导出 region 的
entry / true / false / merge 块及其指令。

用法: D:/Python/python.exe dump_ternary_region.py <pyc路径> [函数名]
"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

_orig = RegionASTGenerator._generate_ternary
_state = {'shown': 0, 'want': None}


def dump_block(tag, b, depth):
    pad = '  ' * depth
    if b is None:
        print('%s%-12s = None' % (pad, tag))
        return
    off = getattr(b, 'start_offset', '?')
    print('%s%-12s off=%s' % (pad, tag, off))
    ins = getattr(b, 'instructions', None) or []
    for i in ins:
        print('%s   %4d %s' % (pad, i.offset,
                               i.opname + (' ' + str(i.argval)
                                           if i.arg is not None else '')))


def patched(self, region, *a, **kw):
    if _state['shown'] == 0:
        _state['shown'] = 1
        print('=== TernaryRegion 结构 ===')
        blocks = getattr(region, 'blocks', []) or []
        print('blocks offsets = %s'
              % sorted(getattr(b, 'start_offset', -1) for b in blocks))
        for attr in ('entry', 'cond_block', 'true_block', 'false_block',
                     'merge_block'):
            dump_block(attr, getattr(region, attr, None), 1)
        print('merge_context =', getattr(region, 'merge_context', None))
        print('value_target  =', getattr(region, 'value_target', None))
        print('--- cond_block 之外、属于本 region 的块 ---')
        seen = {id(getattr(region, attr, None))
                for attr in ('entry', 'cond_block', 'true_block',
                             'false_block', 'merge_block')}
        for b in blocks:
            if id(b) in seen:
                continue
            dump_block('block', b, 1)
        print('=== end ===')
    return _orig(self, region, *a, **kw)


RegionASTGenerator._generate_ternary = patched


def main():
    from pycdc import decompile_pyc
    decompile_pyc(sys.argv[1], use_cfg=True)


if __name__ == '__main__':
    main()
