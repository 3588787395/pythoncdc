"""Round 33: 诊断类体 NOP 在 _generate_instructions_content 的处理路径。"""
import sys, marshal, types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
PYC = ROOT + r'\site-packages\fly\simtradding\ptradeAccount.pyc'


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def main():
    pyc = load_code(PYC)
    cls = [c for c in pyc.co_consts if isinstance(c, types.CodeType) and c.co_name == 'PtradeAccount'][0]
    print('类体 co_code len:', len(cls.co_code))

    from core.cfg.cfg_builder import build_cfg
    from core.cfg.ast_generator_v2 import ASTGeneratorV2
    cfg = build_cfg(cls, 'PtradeAccount')
    blocks = cfg.get_blocks_in_order()
    print('CFG blocks:', len(blocks))

    entry = cfg.entry_block
    print('entry block:', entry.start_offset, '->', entry.end_offset,
          'instr count:', len(entry.instructions))

    # 打印入口块全部指令（前 40 + NOP 位置）
    instrs = entry.instructions
    print('\n--- entry block instructions (%d) ---' % len(instrs))
    for i, ins in enumerate(instrs):
        mark = ''
        if ins.opname == 'NOP':
            mark = '  <<< NOP'
        if i < 40 or ins.opname == 'NOP':
            print('  [%3d] off=%4d %-22s line=%s%s' % (i, ins.offset, ins.opname, ins.starts_line, mark))

    gen = ASTGeneratorV2(cfg, recursive=True)
    gen.structures = gen.structured_analyzer.analyze()
    print('\nstructures:', [(s.__class__.__name__, s.struct_type if hasattr(s, 'struct_type') else '?')
                             for s in gen.structures])

    # 手动复算 _generate_instructions_content 的 NOP 分支判定
    non_jump_instrs = [ins for ins in instrs if ins.opname not in ('JUMP_ABSOLUTE', 'FOR_ITER', 'FOR_ITER_RANGE')]
    first_nop_idx = -1
    nop_count = 0
    has_cond_jump = False
    for i, ins in enumerate(non_jump_instrs):
        if ins.opname == 'NOP':
            if first_nop_idx == -1:
                first_nop_idx = i
            nop_count += 1
        elif ins.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                            'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                            'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
            has_cond_jump = True
    print('\nnon_jump_instrs:', len(non_jump_instrs), 'first_nop_idx:', first_nop_idx,
          'nop_count:', nop_count, 'has_cond_jump:', has_cond_jump)
    print('走过滤分支?:', nop_count > 1 or not has_cond_jump)

    # 复算过滤后保留的指令（新的修复逻辑）
    filtered = [
        ins for i, ins in enumerate(non_jump_instrs)
        if ins.opname != 'NOP' or gen._is_orphan_nop_statement(non_jump_instrs, i)
    ]
    kept_nops = [ins for ins in filtered if ins.opname == 'NOP']
    print('修复后过滤指令数:', len(filtered), '保留 NOP:', [(ins.offset, ins.starts_line) for ins in kept_nops])

    # 对每个 NOP 打印 _is_orphan_nop_statement 的判定细节
    print('\n--- NOP 孤立判定细节 ---')
    for i, ins in enumerate(non_jump_instrs):
        if ins.opname == 'NOP':
            prev = nxt = None
            for j in range(i - 1, -1, -1):
                if non_jump_instrs[j].opname not in ('RESUME', 'CACHE', 'NOP'):
                    prev = non_jump_instrs[j]
                    break
            for j in range(i + 1, len(non_jump_instrs)):
                if non_jump_instrs[j].opname not in ('RESUME', 'CACHE', 'NOP'):
                    nxt = non_jump_instrs[j]
                    break
            r = gen._is_orphan_nop_statement(non_jump_instrs, i)
            print('  NOP@%d line=%s prev=%s(%s) nxt=%s(%s) -> orphan=%s' % (
                ins.offset, ins.starts_line,
                prev.opname if prev else None, prev.argval if prev else '',
                nxt.opname if nxt else None, str(nxt.argval)[:30] if nxt else '',
                r))

    # 直接调用 _generate_instructions_content 看输出
    print('\n--- 调用 _generate_instructions_content ---')
    out = gen._generate_instructions_content(instrs)
    if isinstance(out, list):
        print('输出语句数:', len(out))
        for s in out:
            if isinstance(s, dict):
                ph = ' [NOP-PLACEHOLDER]' if s.get('_nop_placeholder') else ''
                print('  %-12s line=%s%s' % (s.get('type'), s.get('lineno'), ph))
    else:
        print('输出:', out)


if __name__ == '__main__':
    main()
