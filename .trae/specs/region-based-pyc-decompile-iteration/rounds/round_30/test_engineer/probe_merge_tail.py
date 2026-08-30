"""探测 BoolOpRegion merge_block 尾部指令的去向（_downstream_region_entry vs 通用生成）。

用法: D:/Python/python.exe probe_merge_tail.py <pyc路径> <offset> [opname]
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
        mb = region.merge_block
        print('merge_block off=%s' % getattr(mb, 'start_offset', '?'))
        print('  instrs =', [i.offset for i in mb.instructions])
        ds = self._downstream_region_entry(mb, region)
        print('  _downstream_region_entry ->', type(ds).__name__ if ds else None, end='')
        if ds is not None:
            print('  blocks=%s' % sorted(
                getattr(b, 'start_offset', -1) for b in (getattr(ds, 'blocks', None) or [])))
        else:
            print()
        # 模拟 R78：把 STORE_ATTR 之后的指令交给通用块生成
        _mb = [i for i in mb.instructions
               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        sa = next((k for k, i in enumerate(_mb) if i.opname == 'STORE_ATTR'), None)
        if sa is not None:
            store = _mb[sa]
            idx = mb.instructions.index(store)
            rem = mb.instructions[idx + 1:]
            print('  remaining after STORE_ATTR(%d) = %d instr  %s'
                  % (store.offset, len(rem), [i.offset for i in rem][:24]))
            orig = mb.instructions
            mb.instructions = rem
            try:
                out = self._generate_block_statements(mb)
            finally:
                mb.instructions = orig
            print('  _generate_block_statements -> %d stmt(s)' % (len(out) if out else 0))
            for s in (out or []):
                print('     ', str(s)[:150])
            # 假设：块尾的条件跳转使生成器把整块当成条件块，前面语句被丢弃。
            # 去掉尾部跳转后再试。
            if rem and rem[-1].opname.startswith(('POP_JUMP', 'JUMP_IF', 'FOR_ITER')):
                rem2 = rem[:-1]
                print('  --- 去掉尾部 %s(%d) 后重试 (%d instr) ---'
                      % (rem[-1].opname, rem[-1].offset, len(rem2)))
                mb.instructions = rem2
                try:
                    out2 = self._generate_block_statements(mb)
                finally:
                    mb.instructions = orig
                print('  -> %d stmt(s)' % (len(out2) if out2 else 0))
                for s in (out2 or []):
                    print('     ', str(s)[:150])
                # 再试：只交给通用语句构建器
                print('  --- _build_statements_from_instructions(rem2) ---')
                try:
                    out3 = self._build_statements_from_instructions(rem2, mb)
                except Exception as e:
                    out3 = None
                    print('     EXC', type(e).__name__, e)
                if out3:
                    print('  -> %d stmt(s)' % len(out3))
                    for s in out3:
                        print('     ', str(s)[:150])
                # 按「最后一条语句归约入口」切分（尾部跳转不参与搜索）
                search = rem2
                last = -1
                for k, ins in enumerate(search):
                    if self._is_statement_reduction_entry(ins):
                        last = k
                print('  --- 按最后一条归约入口切分: idx=%d -> %s ---'
                      % (last, search[last].offset if last >= 0 else None))
                if last >= 0:
                    head = search[:last + 1]
                    tail = search[last + 1:] + [rem[-1]]
                    print('      head=%s' % [i.offset for i in head])
                    print('      tail=%s' % [i.offset for i in tail])
                    st = self._build_statements_from_instructions(head, mb)
                    print('      head -> %d stmt(s)' % (len(st) if st else 0))
                    mb.instructions = tail
                    try:
                        out4 = self._generate_block_statements(mb)
                    finally:
                        mb.instructions = orig
                    print('      tail -> %d stmt(s)' % (len(out4) if out4 else 0))
                    for s in (out4 or []):
                        print('         ', str(s)[:130])
    return _orig_boolop(self, region, *a, **kw)


RegionASTGenerator._generate_boolop = patched_boolop


def main():
    from pycdc import decompile_pyc
    _state['offset'] = int(sys.argv[2])
    _state['opname'] = sys.argv[3] if len(sys.argv) > 3 else None
    decompile_pyc(sys.argv[1], use_cfg=True)


if __name__ == '__main__':
    main()
