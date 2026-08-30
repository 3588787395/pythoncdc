"""对比两种前缀语句构建器对同一段前缀指令的输出。

用法: D:/Python/python.exe probe_stmt_builder.py <pyc路径> <offset> [opname]
"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

_orig_boolop = RegionASTGenerator._generate_boolop
_state = {'offset': None, 'opname': None, 'done': False}


def covers(region):
    for b in (getattr(region, 'blocks', None) or []):
        for i in (getattr(b, 'instructions', None) or []):
            if getattr(i, 'offset', None) == _state['offset']:
                if _state['opname'] is None or i.opname == _state['opname']:
                    return True
    return False


def patched_boolop(self, region, *a, **kw):
    if not _state['done'] and covers(region):
        _state['done'] = True
        chain = getattr(region, 'op_chain', None) or []
        if chain:
            blk = chain[0][0]
            pre = self.region_analyzer.identify_block_prefix_instructions(blk)
            print('prefix instrs =', [i.offset for i in pre])
            last = -1
            for idx, ins in enumerate(pre):
                if self._is_statement_reduction_entry(ins):
                    last = idx
            cut = pre[:last + 1] if last >= 0 else []
            print('cut at idx=%d -> %s' % (last, [i.offset for i in cut]))
            print()
            print('--- A: _build_prefix_stmt_list ---')
            try:
                for s in self._build_prefix_stmt_list(cut, blk):
                    print('   ', str(s)[:200])
            except Exception as e:
                print('    EXC', e)
            print('--- B: _build_statements_from_instructions ---')
            try:
                r = self._build_statements_from_instructions(cut, blk)
                if r is None:
                    print('    None')
                else:
                    for s in r:
                        print('   ', str(s)[:200])
            except Exception as e:
                print('    EXC', type(e).__name__, e)
            print('--- end ---')
    return _orig_boolop(self, region, *a, **kw)


RegionASTGenerator._generate_boolop = patched_boolop


def main():
    from pycdc import decompile_pyc
    _state['offset'] = int(sys.argv[2])
    _state['opname'] = sys.argv[3] if len(sys.argv) > 3 else None
    decompile_pyc(sys.argv[1], use_cfg=True)


if __name__ == '__main__':
    main()
