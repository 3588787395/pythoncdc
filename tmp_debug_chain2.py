"""Trace op_type computation step by step"""
import sys
import dis
sys.path.insert(0, '/workspace')

# Patch _detect_boolop_conditional_chain to add prints
from core.cfg import region_analyzer as ra_mod
original_detect = ra_mod.RegionAnalyzer._detect_boolop_conditional_chain

def traced_detect(self, start_block, claimed, skip_claimed_check=False):
    chain = []
    current = start_block
    visited = set()
    BOOLOP_CHAIN_JUMPS = ra_mod.FORWARD_CONDITIONAL_JUMP_OPS | ra_mod.SHORT_CIRCUIT_JUMP_OPS
    first_jump_type = None
    while current and current.start_offset not in visited:
        visited.add(current.start_offset)
        last = current.get_last_instruction()
        if not last or last.opname not in BOOLOP_CHAIN_JUMPS:
            print(f"  iter: block {current.start_offset} - last instr not boolop jump ({last.opname if last else None}), breaking")
            break
        if current in self.block_to_region:
            existing_reg = self.block_to_region.get(current)
            if isinstance(existing_reg, ra_mod.BoolOpRegion):
                print(f"  iter: block {current.start_offset} - already in BoolOpRegion, breaking")
                break
        cur_jump_type = 'forward' if last.opname in ra_mod.FORWARD_CONDITIONAL_JUMP_OPS else 'short_circuit'
        if first_jump_type is None:
            first_jump_type = cur_jump_type
        op_type = 'and' if ('FALSE' in last.opname or '_IF_NONE' in last.opname) else 'or'
        print(f"  iter: block {current.start_offset} - last={last.opname} argval={last.argval} - op_type={op_type}")
        chain.append((current, op_type))
        # Check discriminator
        if last.argval is not None and chain:
            _sc_target = self.cfg.get_block_by_offset(last.argval)
            if _sc_target is not None:
                _sc_target_last = _sc_target.get_last_instruction()
                _target_is_exit = (_sc_target_last is None
                                   or _sc_target_last.opname in ('RETURN_VALUE', 'RETURN_CONST'))
                print(f"    discriminator: _sc_target=block {_sc_target.start_offset}, _target_is_exit={_target_is_exit}")
                if (not _target_is_exit and _sc_target_last
                        and _sc_target_last.opname in BOOLOP_CHAIN_JUMPS
                        and _sc_target_last.argval is not None):
                    _is_or_short_circuit = 'TRUE' in _sc_target_last.opname
                    _actual_op = 'or' if _is_or_short_circuit else 'and'
                    _is_non_first = len(chain) >= 2
                    _should_fire = (_is_non_first or _actual_op != op_type)
                    print(f"    discriminator: _actual_op={_actual_op}, _is_non_first={_is_non_first}, _should_fire={_should_fire}")
        # Move to next block (fall-through)
        succs = list(current.conditional_successors)
        if len(succs) != 2:
            print(f"    succs != 2, breaking")
            break
        ft_succ = next((s for s in succs if s.start_offset != last.argval), None)
        if ft_succ is None:
            print(f"    no ft_succ, breaking")
            break
        current = ft_succ
        print(f"    → next block {current.start_offset}")
    print(f"  FINAL chain: {[(b.start_offset, op) for b, op in chain]}")
    return chain if chain else None

ra_mod.RegionAnalyzer._detect_boolop_conditional_chain = traced_detect

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator


SOURCE = """if a or (b if c else d):
    pass"""

code = compile(SOURCE, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
