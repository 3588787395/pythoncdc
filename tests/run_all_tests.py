#!/usr/bin/env python3
"""Run all tests (original + additional batches) and count errors"""

import sys
from pathlib import Path
import shutil

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.cfg import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CFGCodeGenerator

ERROR_DIRS = [
    Path(__file__).parent / "newno",
    Path(__file__).parent / "newno_additional",
    Path(__file__).parent / "newno_additional_2",
    Path(__file__).parent / "newno_additional_3",
    Path(__file__).parent / "newno_additional_4",
]

TOTAL_SUCCESS = 0
TOTAL_FAIL = 0

def extract_func(code, name='test_func'):
    for c in code.co_consts:
        if hasattr(c, 'co_name') and c.co_name == name:
            return c
    return None

for error_dir in ERROR_DIRS:
    if not error_dir.exists():
        continue
    
    dir_success = 0
    dir_fail = 0
    
    for error_file in sorted(error_dir.glob("*.py")):
        content = error_file.read_text(encoding='utf-8')
        parts = content.split("# Decompiled:", 1)
        if len(parts) != 2:
            continue
        
        source_part = parts[0]
        source_lines = source_part.split('\n')
        source = '\n'.join(source_lines[1:])  # Skip comment line
        
        try:
            orig = compile(source, '<o>', 'exec')
            func = extract_func(orig)
            if not func:
                func = orig
            
            cfg = CFGBuilder().build(func)
            gen = RegionASTGenerator(cfg)
            ast_dict = gen.generate()
            code_gen = CFGCodeGenerator()
            decompiled = code_gen.generate(ast_dict)
            
            if decompiled is None:
                dir_fail += 1
                continue
            
            try:
                recomp = compile(decompiled, '<r>', 'exec')
                recomp_func = extract_func(recomp)
                if not recomp_func:
                    recomp_func = recomp
                
                if func.co_code == recomp_func.co_code:
                    dir_success += 1
                else:
                    dir_fail += 1
            except Exception:
                dir_fail += 1
        except Exception:
            dir_fail += 1
    
    TOTAL_SUCCESS += dir_success
    TOTAL_FAIL += dir_fail
    print(f"{error_dir.name}: Success={dir_success}, Fail={dir_fail}")

print(f"\n{'='*60}")
print(f"TOTAL: Success={TOTAL_SUCCESS}, Fail={TOTAL_FAIL}")
print(f"Success rate: {TOTAL_SUCCESS/(TOTAL_SUCCESS+TOTAL_FAIL)*100:.1f}%")
