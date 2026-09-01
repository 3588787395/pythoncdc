"""Probe: 打印覆盖指定 offset 的区域完整属性（then/else blocks 等）。"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

TARGET = 1298
_orig = RegionASTGenerator._generate_region
_done = set()


def dump_attrs(region):
    rtype = type(region).__name__
    print('=== %s (id=%s) ===' % (rtype, id(region)))
    for attr in ('region_type', 'entry', 'condition_block', 'true_block',
                 'false_block', 'merge_block', 'then_blocks', 'else_blocks',
                 'body_blocks', 'elif_conditions', 'elif_bodies',
                 'elif_final_else'):
        v = getattr(region, attr, '<missing>')
        if v is None:
            print('  %s = None' % attr)
        elif isinstance(v, list):
            print('  %s = [%s]' % (attr, ', '.join(str(getattr(b, 'start_offset', b)) for b in v)))
        elif hasattr(v, 'start_offset'):
            print('  %s = block@%s' % (attr, v.start_offset))
        elif attr == 'region_type':
            print('  region_type = %s' % v)
        else:
            print('  %s = %r' % (attr, v))


def patched(self, region, *a, **kw):
    blocks = list(getattr(region, 'blocks', []) or [])
    for b in blocks:
        for i in (getattr(b, 'instructions', None) or []):
            if i.offset == TARGET and id(region) not in _done:
                _done.add(id(region))
                dump_attrs(region)
                break
    return _orig(self, region, *a, **kw)


RegionASTGenerator._generate_region = patched

from pycdc import decompile_pyc
decompile_pyc(sys.argv[1], use_cfg=True)
print('=== dumped %d regions ===' % len(_done))
