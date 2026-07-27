"""R10 测试工程师：验证 minimal repros 的字节码一致性。"""
import sys
import os
import types
import importlib.util

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

REPRO_DIR = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_10/test_engineer/minimal_repros'


def code_normalize(code):
    norm_consts = []
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            norm_consts.append(code_normalize(c))
        else:
            norm_consts.append(c)
    return (
        code.co_code,
        tuple(norm_consts),
        code.co_argcount,
        code.co_posonlyargcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        tuple(code.co_cellvars),
        tuple(code.co_freevars),
        tuple(code.co_varnames),
        tuple(code.co_names),
        code.co_stacksize,
        code.co_flags,
    )


def verify_repro(path):
    """加载 repro 文件，提取 SOURCE，反编译，比较字节码。"""
    spec = importlib.util.spec_from_file_location('m', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    src = mod.SOURCE
    try:
        orig_code = compile(src, path, 'exec')
        cfg = CFGBuilder().build(orig_code)
        analyzer = RegionAnalyzer(cfg)
        generator = RegionASTGenerator(cfg, analyzer)
        tree = generator.generate()
        decompiled = CodeGenerator().generate(tree)
        decomp_code = compile(decompiled, path + '.decomp', 'exec')
    except Exception as e:
        return False, f"EXC: {e}", src, ''
    if code_normalize(orig_code) == code_normalize(decomp_code):
        return True, "OK", src, decompiled
    return False, "MISMATCH", src, decompiled


def main():
    files = sorted(f for f in os.listdir(REPRO_DIR) if f.startswith('repro_') and f.endswith('.py'))
    passed = 0
    failed = 0
    for f in files:
        path = os.path.join(REPRO_DIR, f)
        ok, msg, src, decomp = verify_repro(path)
        status = 'PASS' if ok else 'FAIL'
        print(f"  [{status}] {f}  ({msg})")
        if ok:
            passed += 1
        else:
            failed += 1
            # show first diff lines
            src_lines = src.strip().split('\n')
            dec_lines = decomp.strip().split('\n')
            print(f"    --- SOURCE ---")
            for ln in src_lines[:8]:
                print(f"    | {ln}")
            print(f"    --- DECOMPILED ---")
            for ln in dec_lines[:8]:
                print(f"    | {ln}")
    print(f"\n=== R10 repros: {passed} passed, {failed} failed ===")


if __name__ == '__main__':
    main()
