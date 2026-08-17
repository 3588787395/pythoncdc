#!/usr/bin/env python3
"""Round 07: Precisely trace all_blocks construction for TryExceptRegion(entry=474)."""
import sys, os, dis, types, marshal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.region_analyzer import CONDITIONAL_JUMP_OPS

PYC_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_test.pyc')

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    return code

def collect_all_code_objects(code, prefix=''):
    from collections import OrderedDict
    result = OrderedDict()
    name = prefix + code.co_name if prefix else code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.' if prefix else code.co_name + '.'
            result.update(collect_all_code_objects(const, child_prefix))
    return result

def main():
    orig_code = load_code_from_pyc(PYC_PATH)
    all_codes = collect_all_code_objects(orig_code)
    target_name = '<module>.exception_handling_examples'
    target_code = all_codes[target_name]
    
    cfg = build_cfg(target_code)
    ra = RegionAnalyzer(cfg, parent_code=target_code)
    
    # Parse exception table
    handler_infos = ra._parse_exception_table()
    
    # Process handler_infos in order, tracking what happens for entry=474
    for i, handler_info in enumerate(handler_infos):
        if handler_info.get('try_start') != 474 or handler_info.get('try_end') != 502:
            continue
        
        print(f"=== Processing handler_info[{i}]: try_start=474, try_end=502, handler=504 ===")
        
        # Replicate the logic from _identify_try_except_regions
        handler_type = handler_info.get('handler_type', 'except')
        try_start = handler_info['try_start']
        try_end = handler_info['try_end']
        handler_start_offset = handler_info['handler_start']
        
        handler_entry_block = cfg.get_block_by_offset(handler_start_offset)
        entry_block = cfg.get_block_by_offset(try_start)
        
        # Collect try_blocks
        excluded_offsets = set()
        for other_info in handler_infos:
            if other_info is handler_info:
                continue
            if not (other_info['try_start'] < handler_info['try_start'] and
                    handler_info['try_end'] <= other_info['try_end']):
                for key in ('handler_start', 'finally_handler_start'):
                    offset = other_info.get(key)
                    if offset:
                        excluded_offsets.add(offset)
        
        print(f"  excluded_offsets: {excluded_offsets}")
        
        try_blocks = []
        for block in cfg.get_blocks_in_order():
            if not any(try_start <= instr.offset < try_end for instr in block.instructions):
                continue
            if block == handler_entry_block:
                continue
            if block.start_offset in excluded_offsets:
                continue
            if block in ra.block_to_region:
                continue
            try_blocks.append(block)
        
        print(f"  try_blocks: {[b.start_offset for b in try_blocks]}")
        
        # Collect handler chain
        all_except_handlers = []
        all_handler_entry_blocks = []
        all_handler_blocks_set = set()
        
        handler_body_blocks = ra._collect_handler_chain(
            handler_info['handler_start'], all_except_handlers,
            all_handler_entry_blocks, all_handler_blocks_set)
        
        print(f"  all_except_handlers: {[(et, en, [b.start_offset for b in hbs]) for et, en, hbs in all_except_handlers]}")
        print(f"  all_handler_entry_blocks: {[b.start_offset for b in all_handler_entry_blocks]}")
        print(f"  all_handler_blocks_set: {[b.start_offset for b in all_handler_blocks_set]}")
        
        finally_blocks = []
        
        # Pattern C fix
        if all_except_handlers:
            _pop_except_blocks = [b for b in all_handler_blocks_set
                                  if any(i.opname == 'POP_EXCEPT' for i in b.instructions)]
            print(f"  _pop_except_blocks: {[b.start_offset for b in _pop_except_blocks]}")
            if _pop_except_blocks:
                _extra_handler_blocks = set()
                _visited_eh = set()
                _worklist_eh = []
                for peb in _pop_except_blocks:
                    for succ in peb.successors:
                        if succ in peb.exception_successors:
                            continue
                        if succ in all_handler_blocks_set:
                            continue
                        if succ in ra.block_to_region:
                            continue
                        if succ not in try_blocks:
                            continue
                        _worklist_eh.append(succ)
                print(f"  Pattern C initial worklist: {[b.start_offset for b in _worklist_eh]}")
                while _worklist_eh:
                    _blk = _worklist_eh.pop()
                    if _blk in _visited_eh:
                        continue
                    if _blk in all_handler_blocks_set:
                        continue
                    if _blk in ra.block_to_region:
                        continue
                    _visited_eh.add(_blk)
                    _extra_handler_blocks.add(_blk)
                    _last_instr = _blk.get_last_instruction()
                    if _last_instr and _last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
                        continue
                    for _succ in _blk.successors:
                        if _succ in _blk.exception_successors:
                            continue
                        if _succ in all_handler_blocks_set:
                            continue
                        if _succ in ra.block_to_region:
                            continue
                        if _succ in _visited_eh:
                            continue
                        _worklist_eh.append(_succ)
                if _extra_handler_blocks:
                    all_handler_blocks_set |= _extra_handler_blocks
                    print(f"  Pattern C extra blocks: {[b.start_offset for b in _extra_handler_blocks]}")
        
        all_blocks = set(try_blocks) | all_handler_blocks_set | set(finally_blocks)
        print(f"  all_blocks (after Pattern C): {[b.start_offset for b in all_blocks]}")
        
        # if-branch expansion
        if try_blocks and all_except_handlers:
            _expanded_try = list(try_blocks)
            _try_block_set = set(try_blocks)
            _handler_offset = handler_info['handler_start']
            _try_start_min = min(b.start_offset for b in try_blocks)
            _changed = True
            while _changed:
                _changed = False
                for _tb in list(_expanded_try):
                    _tb_last = _tb.get_last_instruction()
                    if not _tb_last:
                        continue
                    if _tb_last.opname not in CONDITIONAL_JUMP_OPS:
                        continue
                    for _succ in _tb.successors:
                        if _succ in _try_block_set:
                            continue
                        if _succ in all_handler_blocks_set:
                            continue
                        if _succ in ra.block_to_region:
                            continue
                        if _succ == handler_entry_block:
                            continue
                        if any(i.opname == 'PUSH_EXC_INFO' for i in _succ.instructions):
                            continue
                        if _succ.start_offset < _try_start_min:
                            continue
                        if _succ.start_offset >= _handler_offset:
                            continue
                        _expanded_try.append(_succ)
                        _try_block_set.add(_succ)
                        _changed = True
            if len(_expanded_try) > len(try_blocks):
                try_blocks = _expanded_try
                all_blocks = set(try_blocks) | all_handler_blocks_set | set(finally_blocks)
                print(f"  if-branch expansion added: {[b.start_offset for b in try_blocks if b not in _try_block_set]}")
            else:
                print(f"  if-branch expansion: no change")
        
        print(f"  all_blocks (after if-branch expansion): {[b.start_offset for b in all_blocks]}")
        
        # Explicit return blocks (Pattern C2)
        if handler_type == 'except' and handler_entry_block is not None:
            _explicit_return_blocks = []
            _try_block_set_r = set(try_blocks)
            _handler_offset_r = handler_entry_block.start_offset
            _seen_r = set()
            for tb in try_blocks:
                for succ in tb.successors:
                    if succ in tb.exception_successors:
                        continue
                    if succ in _seen_r:
                        continue
                    _seen_r.add(succ)
                    if succ.start_offset >= _handler_offset_r:
                        continue
                    if succ in _try_block_set_r:
                        continue
                    if succ in all_handler_blocks_set:
                        continue
                    if succ in finally_blocks:
                        continue
                    if succ in all_blocks:
                        continue
                    if succ in ra.block_to_region:
                        continue
                    if succ.start_offset in excluded_offsets:
                        continue
                    if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'CHECK_EXC_MATCH',
                                         'CHECK_EG_MATCH', 'RERAISE', 'POP_EXCEPT') for i in succ.instructions):
                        continue
                    _last_i = succ.get_last_instruction()
                    if _last_i is None or _last_i.opname not in ('RETURN_VALUE', 'RETURN_CONST'):
                        continue
                    _explicit_return_blocks.append(succ)
            if _explicit_return_blocks:
                for _eb in _explicit_return_blocks:
                    if _eb not in try_blocks:
                        try_blocks.append(_eb)
                    all_blocks.add(_eb)
                print(f"  explicit return blocks added: {[b.start_offset for b in _explicit_return_blocks]}")
            else:
                print(f"  explicit return blocks: none")
        
        print(f"  all_blocks (after explicit return): {[b.start_offset for b in all_blocks]}")
        
        # Existing regions check
        for existing_region in ra._filter_regions(ra.regions, TryExceptRegion):
            for block in existing_region.blocks:
                if any(try_start <= instr.offset < try_end for instr in block.instructions):
                    if block not in all_handler_blocks_set and block != handler_entry_block:
                        all_blocks.add(block)
                        print(f"  existing region {existing_region.entry.start_offset} added block@{block.start_offset}")
        
        print(f"  all_blocks (after existing regions): {[b.start_offset for b in all_blocks]}")
        
        # Cleanup blocks search
        cleanup_blocks = []
        cleanup_visited = set()
        search_blocks = list(all_handler_entry_blocks)
        for heb in all_handler_entry_blocks:
            for succ in heb.successors:
                if succ not in all_blocks:
                    search_blocks.append(succ)
        for block in list(all_handler_blocks_set):
            for succ in block.successors:
                if succ not in all_blocks:
                    search_blocks.append(succ)
        
        print(f"  search_blocks for cleanup: {[b.start_offset for b in search_blocks]}")
        
        # Check exception table chain
        _chain_target_set = set()
        for _hb in (finally_blocks or []):
            _chain_target_set.add(_hb.start_offset)
        for _heb in (all_handler_entry_blocks or []):
            _chain_target_set.add(_heb.start_offset)
        for _ab in (all_handler_blocks_set or []):
            _chain_target_set.add(_ab.start_offset)
        if handler_entry_block is not None:
            _chain_target_set.add(handler_entry_block.start_offset)
        
        print(f"  _chain_target_set: {_chain_target_set}")
        
        if cfg.exception_table:
            _chain_entry_ids = set()
            _chain_changed = True
            while _chain_changed:
                _chain_changed = False
                for _ee in cfg.exception_table:
                    if id(_ee) in _chain_entry_ids:
                        continue
                    _ee_start = _ee.get('start', 0)
                    _ee_end = _ee.get('end', 0)
                    _ee_target = _ee.get('target', 0)
                    _in_try_body = (_ee_start >= try_start and _ee_end <= try_end)
                    _starts_at_known = (_ee_start in _chain_target_set)
                    _shares_target = (_ee_target in _chain_target_set)
                    if _in_try_body or _starts_at_known or _shares_target:
                        _chain_entry_ids.add(id(_ee))
                        _chain_target_set.add(_ee_target)
                        _chain_changed = True
                        print(f"  chain added: start={_ee_start}, end={_ee_end}, target={_ee_target}")
            
            for exc_entry in cfg.exception_table:
                if id(exc_entry) not in _chain_entry_ids:
                    continue
                exc_start = exc_entry.get('start', 0)
                exc_end = exc_entry.get('end', 0)
                for blk in cfg.blocks.values():
                    if blk.start_offset in cleanup_visited:
                        continue
                    if blk in all_blocks:
                        continue
                    if any(exc_start <= instr.offset < exc_end for instr in blk.instructions):
                        search_blocks.append(blk)
                        print(f"  exc table search added block@{blk.start_offset} (range [{exc_start},{exc_end}))")
        
        print(f"  search_blocks (after exc table): {[b.start_offset for b in search_blocks]}")
        
        # Process search_blocks
        for block in search_blocks:
            if block.start_offset in cleanup_visited:
                continue
            if block in all_blocks:
                continue
            cleanup_visited.add(block.start_offset)
            is_cleanup = False
            has_reraise = any(instr.opname == 'RERAISE' for instr in block.instructions)
            has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in block.instructions)
            has_copy = any(instr.opname == 'COPY' for instr in block.instructions)
            if has_reraise:
                is_cleanup = True
            elif has_pop_except and has_copy:
                # Simplified check
                pass
            if is_cleanup:
                cleanup_blocks.append(block)
                print(f"  cleanup block@{block.start_offset} (RERAISE)")
                for succ in block.successors:
                    if succ.start_offset not in cleanup_visited and succ not in all_blocks:
                        search_blocks.append(succ)
        
        if cleanup_blocks:
            all_blocks |= set(cleanup_blocks)
        
        print(f"\n  FINAL all_blocks: {sorted([b.start_offset for b in all_blocks])}")
        print(f"  cleanup_blocks: {[b.start_offset for b in cleanup_blocks]}")
        break

if __name__ == '__main__':
    main()
