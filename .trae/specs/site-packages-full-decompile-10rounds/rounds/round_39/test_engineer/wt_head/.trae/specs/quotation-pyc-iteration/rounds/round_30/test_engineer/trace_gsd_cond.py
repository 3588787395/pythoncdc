"""Trace condition extraction for get_str_data IfRegion 762."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg import region_ast_generator as rag_mod
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

PYC = '/workspace/quotation.pyc'


def load_code(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    for c in code_obj.co_consts:
        if isinstance(c, type(code_obj)) and c.co_name == 'get_str_data':
            return c
    return None


# Monkey-patch _if_extract_condition_from_instructions
_orig_extract_cond = rag_mod.RegionASTGenerator._if_extract_condition_from_instructions

def _traced_extract_cond(self, region, cond_block, cond_instrs):
    result = _orig_extract_cond(self, region, cond_block, cond_instrs)
    if isinstance(region, IfRegion) and region.condition_block is not None:
        if region.condition_block.start_offset == 762:
            print(f"[EXTRACT_COND] region entry={region.entry.start_offset if region.entry else None}")
            print(f"  cond_block={cond_block.start_offset}")
            print(f"  cond_instrs={[i.opname for i in cond_instrs]}")
            print(f"  then_blocks={[b.start_offset for b in region.then_blocks]}")
            print(f"  else_blocks={[b.start_offset for b in region.else_blocks]}")
            print(f"  result={result}")
    return result

rag_mod.RegionASTGenerator._if_extract_condition_from_instructions = _traced_extract_cond

# Also trace _if_generate_normal
_orig_gen_normal = rag_mod.RegionASTGenerator._if_generate_normal

def _traced_gen_normal(self, region):
    if isinstance(region, IfRegion) and region.condition_block is not None:
        if region.condition_block.start_offset == 762:
            print(f"\n[GEN_NORMAL] entry={region.entry.start_offset if region.entry else None}")
            print(f"  cond_block={region.condition_block.start_offset}")
            print(f"  then_blocks={[b.start_offset for b in region.then_blocks]}")
            print(f"  else_blocks={[b.start_offset for b in region.else_blocks]}")
            print(f"  merge={region.merge_block.start_offset if region.merge_block else None}")
    return _orig_gen_normal(self, region)

rag_mod.RegionASTGenerator._if_generate_normal = _traced_gen_normal

# Trace _if_generate_then_branch
_orig_then = rag_mod.RegionASTGenerator._if_generate_then_branch

def _traced_then(self, region):
    result = _orig_then(self, region)
    if isinstance(region, IfRegion) and region.condition_block is not None:
        if region.condition_block.start_offset == 762:
            print(f"[THEN_BRANCH] result={result}")
    return result

rag_mod.RegionASTGenerator._if_generate_then_branch = _traced_then


def main():
    co = load_code(PYC)
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    ra.analyze()
    
    # Check region hierarchy
    print("=== Region 762 details ===")
    for r in ra.regions:
        if isinstance(r, IfRegion) and r.condition_block is not None:
            if r.condition_block.start_offset in (762, 788):
                print(f"  IfRegion cond={r.condition_block.start_offset}")
                print(f"    entry={r.entry.start_offset if r.entry else None}")
                print(f"    then={[b.start_offset for b in r.then_blocks]}")
                print(f"    else={[b.start_offset for b in r.else_blocks]}")
                print(f"    merge={r.merge_block.start_offset if r.merge_block else None}")
                print(f"    parent={r.parent}")
                print(f"    children={[c.entry.start_offset if hasattr(c, 'entry') and c.entry else None for c in (r.children or [])]}")
                # Check if there's a BoolOpRegion for these blocks
                for br in ra.regions:
                    if hasattr(br, 'entry') and br.entry is not None:
                        if br.entry.start_offset in (762, 788):
                            print(f"    -> region entry={br.entry.start_offset} type={type(br).__name__}")


if __name__ == '__main__':
    main()
