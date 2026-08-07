"""Apply R46 fix for duplicate pre-statement extraction in BoolOp."""

filepath = 'core/cfg/region_ast_generator.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the target section (around line 22893-22904)
for i in range(len(lines)):
    if i > 22880 and 'elif op_chain:' in lines[i]:
        # Found the elif op_chain: block
        # Find the next line that starts with '            first_chain_block'
        for j in range(i, min(i+20, len(lines))):
            if 'first_chain_block = op_chain[0][0]' in lines[j]:
                # Insert the guard after this line
                indent = '            '
                guard_line = indent + '# [R46 fix] 区域归约算法原则 2（每块唯一归属）：当 first_chain_block\n'
                guard_line += indent + '# 已被 generate() 入口处理提取过前置语句（标记为 generated），不应\n'
                guard_line += indent + '# 在此重复提取。典型场景：a = None; a = a or x.close 中入口块同时\n'
                guard_line += indent + '# 是 BoolOpRegion 的首个 chain block，generate() 的 BoolOpRegion\n'
                guard_line += indent + '# 入口分支已通过 _if_extract_cond_instructions 提取 a = None，\n'
                guard_line += indent + '# 若此处再次提取会导致重复输出。\n'
                guard_check = indent + 'if first_chain_block in self.generated_blocks:\n'
                guard_check += indent + '    pre_stmts = []\n'
                guard_check += indent + 'else:\n'
                
                # Insert the guard after 'first_chain_block = op_chain[0][0]'
                lines.insert(j+1, guard_line)
                # Indent the original code and wrap in else
                for k in range(j+2, len(lines)):
                    if lines[k].startswith('            pre_instrs'):
                        lines[k] = indent + lines[k].lstrip()
                    elif lines[k].startswith('            last_store_idx'):
                        lines[k] = indent + lines[k].lstrip()
                    elif lines[k].startswith('            for idx'):
                        lines[k] = indent + lines[k].lstrip()
                    elif lines[k].startswith('                if'):
                        lines[k] = '                ' + lines[k].lstrip()
                    elif lines[k].startswith('                    last_store_idx'):
                        lines[k] = '                    ' + lines[k].lstrip()
                    elif lines[k].startswith('            if last_store_idx >= 0:'):
                        lines[k] = indent + lines[k].lstrip()
                    elif lines[k].startswith('                filtered_pre_instrs'):
                        lines[k] = '                ' + lines[k].lstrip()
                    elif lines[k].startswith('                pre_stmts ='):
                        lines[k] = '                ' + lines[k].lstrip()
                    elif lines[k].startswith('            else:'):
                        lines[k] = indent + lines[k].lstrip()
                    elif lines[k].startswith('                pre_stmts = []'):
                        lines[k] = '                ' + lines[k].lstrip()
                    elif not lines[k].strip():
                        lines[k] = lines[k]
                    else:
                        break
                
                lines.insert(j+1, guard_check)
                break
        break

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("R46 fix applied successfully!")