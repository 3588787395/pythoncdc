# -*- coding: utf-8 -*-
"""Build specs/cand_r65d3_c1.json: splice an anchor out of the LANDED generator bytes and
pair it with a replacement block, asserting the anchor occurs exactly once.

usage: python -X utf8 -B mk_c1.py
"""
import io
import json

SRC = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
OUT = r'D:/Temp/opencode/r65gate/diag3/specs/cand_r65d3_c1.json'

lines = io.open(SRC, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n').split('\n')
# 1-based inclusive
a, b = 35989, 36018
anchor = '\n'.join(lines[a - 1:b])

REPL = '''                _mb_instrs = []
                if region.merge_block:
                    _mb_instrs = [i for i in region.merge_block.instructions
                                  if i.opname not in ('RESUME', 'NOP', 'CACHE',
                                                      'PUSH_NULL')]
                # [R65-d3 C1] 单元素 f-string 三元区域的「链尾自包含插值 + 跨块待定
                # 调用」归约，把既有 [R63 Fix1]/[R63 Fix2]/[R64-B2] 三条判据接到
                # _generate_ternary 的独立（非链式）merge_ctx=='fstring' 分支上。
                # 识别条件（全部为本区域自己的 cond_block / merge_block 内的同层次
                # 结构身份，无偏移阈值、无函数名、无字面量计数）：
                #   (1) 本区域是 TernaryRegion 且 merge_context=='fstring'，且
                #       merge_block 不是另一个带 container_type 的 TernaryRegion 的
                #       entry（链式路径已在 L35660 之前优先分派，走到这里即单元素）；
                #   (2) cond_block 前缀（栈效应切出的 cond_val_start 之前）以一段
                #       「本地未消费」的被调对象压栈链开头：
                #       [PUSH_NULL]? LOAD_{GLOBAL,NAME,FAST,DEREF} (LOAD_ATTR|
                #       LOAD_METHOD)*，其后继指令不是它的消费者（既不是
                #       FORMAT_VALUE/CALL/STORE_*/COPY/UNARY_*/BINARY_*/COMPARE_OP，
                #       也不是另一条 LOAD_ATTR/LOAD_METHOD）——与
                #       _ternary_pending_callee「callee 在区域入口压栈、在区域出口
                #       消费」同一判据；
                #   (3) merge_block 里第一个 FORMAT_VALUE 操作数恰好格式化链上三元
                #       结果（其段为空），其后每个 FORMAT_VALUE 之前的指令段都能被
                #       _fstring_parts_from_segment 单趟栈模拟解释（段底全为字面量
                #       Constant、段顶即被格式化操作数）——与 [R63 Fix1] 同一判据。
                # 归约方式：(3) 成立时以段为单位自底向上归约 merge_block 尾部，逐段
                #   产出 Constant/FormattedValue，并用 [R64-B2] 的
                #   _r64b1_fv_conversion 把「消费该值的那条 FORMAT_VALUE 自带的操作数
                #   低 2 位」回填到链上三元结果与尾部插值的 conversion；(2) 成立时把
                #   该段 callee 压栈指令从 JoinedStr 的前缀里剔除（它们属于外层
                #   Call.func，不属于字符串片段）；随后依 _try_wrap_fstring_pending_call
                #   （BUILD_STRING+PRECALL/KW_NAMES*+CALL(arg==1)+POP_TOP）把整条区域
                #   归约为 Expr(Call)，CALL 之后的指令依「每块唯一归属」经
                #   post_consumer_extra_stmts 归父语句序列。任一判据不成立即完整退回
                #   既有扫描，不新增逃逸口。
                # AST 映射：Expr(Call(func=<callee 节点>, args=[JoinedStr(...)])) +
                #   后续语句（本例 Return(Constant False)）；退回时仍为既有的
                #   Return/Expr(JoinedStr)。
                _r65_tail_parts = []
                _r65_seg = []
                _r65_fv = 0
                _r65_tail_ok = True
                _r65_chain_conv = None
                for _mi in _mb_instrs:
                    if _mi.opname == 'BUILD_STRING':
                        break
                    if _mi.opname != 'FORMAT_VALUE':
                        _r65_seg.append(_mi)
                        continue
                    if _r65_fv == 0:
                        if _r65_seg:
                            _r65_tail_ok = False
                            break
                        _r65_chain_conv = self._r64b1_fv_conversion(_mi)
                    else:
                        _r65_parsed = self._fstring_parts_from_segment(
                            _r65_seg, _mi)
                        if _r65_parsed is None:
                            _r65_tail_ok = False
                            break
                        _r65_tail_parts.extend(_r65_parsed)
                    _r65_seg = []
                    _r65_fv += 1
                if _r65_seg:
                    _r65_tail_ok = False
                if _r65_tail_ok:
                    if (fstring_parts
                            and fstring_parts[-1].get('type') == 'FormattedValue'):
                        fstring_parts[-1]['conversion'] = _r65_chain_conv or 0
                    fstring_parts.extend(_r65_tail_parts)
                elif region.merge_block:
                    _after_fv = False
                    for _mi in _mb_instrs:
                        if _mi.opname == 'FORMAT_VALUE':
                            _after_fv = True
                            continue
                        if _after_fv:
                            if _mi.opname == 'LOAD_CONST':
                                fstring_parts.append({
                                    'type': 'Constant', 'value': _mi.argval,
                                })
                            elif _mi.opname == 'BUILD_STRING':
                                break
                # [R65-d3 C1] 前缀里的待定 callee 压栈链剔除（判据 (2)）。
                _r65_callee = None
                _r65_cond_blk = region.condition_block
                if (_r65_cond_blk is not None and fstring_parts
                        and cond_val_start is not None and cond_val_start > 0):
                    _r65_pre = cond_block_instrs[:cond_val_start]
                    _r65_k = 0
                    if (_r65_pre and _r65_pre[0].opname == 'PUSH_NULL'):
                        _r65_k = 1
                    if (_r65_k < len(_r65_pre)
                            and _r65_pre[_r65_k].opname in (
                                'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_FAST',
                                'LOAD_DEREF')):
                        _r65_e = _r65_k + 1
                        while (_r65_e < len(_r65_pre)
                               and _r65_pre[_r65_e].opname in (
                                   'LOAD_ATTR', 'LOAD_METHOD')):
                            _r65_e += 1
                        _r65_nxt = (_r65_pre[_r65_e].opname
                                    if _r65_e < len(_r65_pre) else None)
                        _r65_consumers = (
                            'FORMAT_VALUE', 'CALL', 'CALL_FUNCTION', 'COPY',
                            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                            'STORE_DEREF', 'UNARY_NEGATIVE', 'UNARY_NOT',
                            'UNARY_POSITIVE', 'UNARY_INVERT', 'BINARY_OP',
                            'INPLACE_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                            'BUILD_STRING', 'POP_TOP', 'RETURN_VALUE')
                        if _r65_nxt not in _r65_consumers:
                            _r65_callee = self._ternary_pending_callee(_r65_cond_blk)
                            if _r65_callee is not None:
                                fstring_parts = fstring_parts[
                                    (_r65_e - _r65_k - (1 if _r65_pre[
                                        _r65_k].opname == 'PUSH_NULL' else 0)):]
                joined_str = {
                    'type': 'JoinedStr',
                    'values': fstring_parts,
                }
                _r65_stmt = self._try_wrap_fstring_pending_call(
                    region, region.merge_block, joined_str)
                if _r65_stmt is not None:
                    results.append(_r65_stmt)
                    _r65_post = getattr(region, 'post_consumer_extra_stmts', None)
                    if _r65_post:
                        results.extend(_r65_post)
                    return results
                # 检查merge_block是否有RETURN_VALUE
                has_return = False
                if region.merge_block:
                    for instr in region.merge_block.instructions:
                        if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            has_return = True
                            break
                if has_return:
                    results.append({'type': 'Return', 'value': joined_str})
                else:
                    results.append({'type': 'Expr', 'value': joined_str})'''

txt = io.open(SRC, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
n = txt.count(anchor)
print('anchor occurrences in landed bytes =', n)
assert n == 1, 'anchor not unique'
spec = {'file': 'core/cfg/region_ast_generator.py',
        'edits': [{'anchor': anchor, 'repl': REPL}]}
io.open(OUT, 'w', encoding='utf-8', newline='').write(json.dumps(spec, ensure_ascii=False))
print('wrote', OUT, 'repl lines =', REPL.count('\n') + 1,
      'delta lines =', REPL.count('\n') - anchor.count('\n'))
