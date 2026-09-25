# -*- coding: utf-8 -*-
"""diag2 R66: emit candidate spec json files (workspace only, repo untouched)."""
import io
import json

GEN = 'core/cfg/region_ast_generator.py'
SRC = io.open('F:/Downloads/pythoncdc-main/' + GEN, encoding='utf-8-sig',
              newline='').read().replace(chr(13), '')

VIRTUAL = ("'__while_cond_target__', '__compare_target__',\n"
           "                    '__iter_target__', '__return_target__',\n"
           "                    '__fstring_target__'")

ANCH_P2 = (
    "                # \u68c0\u67e5merge_block\u662f\u5426\u6709RETURN_VALUE\n"
    "                has_return = False\n"
    "                if region.merge_block:\n"
    "                    for instr in region.merge_block.instructions:\n"
    "                        if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):\n"
    "                            has_return = True\n"
    "                            break\n")

NEW_P2 = u'''                # [R66-d2 P2] f-string \u8bed\u53e5\u7531 merge \u5757\u5c3e\u90e8 STORE_* \u6d88\u8d39\u65f6\u5f52\u7ea6\u4e3a\u8d4b\u503c\u3002
                # \u8bc6\u522b\u6761\u4ef6: merge_block \u6709\u6548\u6307\u4ee4\u6d41\uff08_m b_instrs\uff09\u4e2d BUILD_STRING \u4e4b\u540e\u7d27\u8ddf\u7684\u9996\u6761
                #   \u8bed\u53e5\u7ea7\u6307\u4ee4\u662f STORE_{FAST,NAME,GLOBAL,DEREF}\uff0c\u4e14\u5176 argval \u4e0e\u672c\u533a\u57df
                #   value_target \u540c\u540d\uff1bvalue_target \u5fc5\u987b\u662f\u771f\u5b9e\u8d4b\u503c\u540d\u2014\u2014\u6392\u9664\u4e0e\u4e0b\u65b9 store \u5206\u652f
                #   \u540c\u4e00\u4efd\u5185\u90e8\u865a\u62df target \u679a\u4e3e\uff08pythoncdc \u4ec5 5 \u4e2a __xxx_target__\uff09\u3002
                #   \u4e0e _try_build_ternary_chained_container \u51fa\u53e3\u300cBUILD_STRING \u540e\u9996\u4e2a
                #   STORE_* \u21d2 Assign\u300d\u540c\u5c42\u6b21\u3001\u540c\u5224\u636e\uff0c\u4e0d\u542b\u51fd\u6570\u540d/\u504f\u79fb/\u9608\u503c\u6761\u4ef6\u3002
                # \u5f52\u7ea6\u65b9\u5f0f: joined_str \u5f52\u7ea6\u4e3a Assign(targets=[Name(vt)], value=JoinedStr)\uff1b
                #   STORE \u4e4b\u540e\u7684\u5269\u4f59\u6307\u4ee4\u4e0d\u5728\u672c\u5206\u652f\u91cd\u590d\u53d1\u5c04\uff0c\u4ecd\u7531\u533a\u57df\u5916\u7684\u5757\u8d70\u67e5\u6309
                #   \u300c\u6bcf\u5757\u552f\u4e00\u5f52\u5c5e\u300d\u5904\u7406\uff08\u4e0d\u63d0\u524d\u8fd4\u56de\u3001\u4e0d\u6269\u5927 generated_blocks\uff09\u3002
                # AST \u6620\u5c04: x = f'...'\u3001\u540e\u7ee7\u8bed\u53e5\u4fdd\u7559\uff0c\u4e0d\u518d\u88ab merge \u5757\u91cc\u5c5e\u4e8e\u4e0b\u4e00\u6761
                #   \u8bed\u53e5\u7684 RETURN_VALUE \u8bf1\u5bfc\u51fa Return(JoinedStr)\u3002
                _p2_store_target = None
                if region.value_target and str(region.value_target) not in (
                        %(virt)s):
                    _p2_seen_bs = False
                    for _p2_i in _mb_instrs:
                        if not _p2_seen_bs:
                            if _p2_i.opname == 'BUILD_STRING':
                                _p2_seen_bs = True
                            continue
                        if _p2_i.opname in ('STORE_FAST', 'STORE_NAME',
                                            'STORE_GLOBAL', 'STORE_DEREF'):
                            if str(_p2_i.argval) == str(region.value_target):
                                _p2_store_target = str(_p2_i.argval)
                            break
                        break
                if _p2_store_target is not None:
                    results.append({
                        'type': 'Assign',
                        'targets': [{'type': 'Name',
                                     'id': _p2_store_target, 'ctx': 'Store'}],
                        'value': joined_str,
                    })
                    return results
''' % {'virt': VIRTUAL}

NEW_P2 = NEW_P2.replace('_m b_instrs', '_mb_instrs')

spec = {'file': GEN, 'anchor': ANCH_P2, 'repl': NEW_P2 + ANCH_P2}
assert SRC.count(ANCH_P2) == 1, SRC.count(ANCH_P2)
io.open('specs/cand_r66_p2_storeepi.json', 'w', encoding='utf-8').write(
    json.dumps(spec, ensure_ascii=False, indent=1))
print('p2 spec written, anchor count 1, new lines',
      NEW_P2.count('\n'))
