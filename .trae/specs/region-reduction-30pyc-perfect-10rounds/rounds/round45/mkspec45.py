"""Write the R45-A single-file spec from the landed bytes (anchor taken verbatim)."""
import io
import json

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r43gate'
rel = 'core/cfg/region_ast_generator.py'
src = io.open(REPO + '/' + rel, encoding='utf-8-sig', newline='').read()
u = src.replace('\r\n', '\n')
lines = u.split('\n')
anchor = '\n'.join(lines[12514:12520]) + '\n' + lines[12520] + '\n'
assert u.count(anchor) == 1, 'anchor occurrences=%d' % u.count(anchor)
print('ANCHOR >>>\n%s<<<' % anchor)

INS = '''        # 区域归约算法原则 2（每块唯一归属）+ 原则 4（父引用子入口）（R45-A）：
        # 链的 merge 块可被链内某个臂的嵌套 IfRegion 取得归属（作其 else 臂），
        # 此时该块无人发射：链的 elif 发射路径只读 elif_conditions/elif_bodies/
        # elif_final_else，而被链吞并的内层区域不独立发射其 else 臂。
        # 同层判据（只读结构事实）：
        #   ① merge 块不在本链 blocks 归属集内，且本链某后代区域认领它；
        #   ② 本链中存在块以正常后继指向它（臂汇入 ⇒ 链后代码可达）；
        #   ③ 它不是隐式 return None 块（隐式返回由编译器补齐）；
        #   ④ 此刻尚未被任何发射登记（后代若已发射则不重复）；
        #   ⑤ 未经 trailing_return / _r57 / _r91 任一路径承担。
        _mb45 = region.merge_block
        if (_mb45 is not None and trailing_return is None
                and not _r91_post_if_blocks and _mb45 not in (_r57_shared_mb or [])
                and _mb45 not in region.blocks
                and region.find_descendant_region_for_block(_mb45, (IfRegion,)) is not None
                and _mb45.start_offset not in self.generated_offsets
                and any(_mb45 in (getattr(_b45, 'successors', None) or [])
                        for _b45 in region.blocks)):
            _mb45_meaningful = [i for i in _mb45.instructions
                                if i.opname not in ('RESUME', 'NOP', 'CACHE')]
            if not self._is_implicit_return_block(_mb45_meaningful):
                _tail45 = self._generate_block_statements(_mb45)
                if _tail45:
                    self.generated_blocks.add(_mb45)
                    self.generated_offsets.add(_mb45.start_offset)
                    if isinstance(result, list):
                        result = result + _tail45
                    else:
                        result = [result] + _tail45
'''
repl = anchor.replace(lines[12520] + '\n', INS + lines[12520] + '\n')
assert repl != anchor
spec = {'file': rel, 'anchor': anchor, 'repl': repl, 'count': 1}
json.dump(spec, io.open(ROOT + '/spec_r45a.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('wrote spec, insert lines=%d' % INS.count('\n'))
