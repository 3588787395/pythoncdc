"""B76 取证：hook _generate_boolop 捕获 UnboundLocalError 完整传播栈"""
import sys, io, traceback
sys.path.insert(0, r"f:\Downloads\pythoncdc-main")
import core.cfg.region_ast_generator as rag

orig_gb = rag.RegionASTGenerator._generate_boolop


def patched_gb(self, region, skip_store_targets=None):
    try:
        return orig_gb(self, region, skip_store_targets=skip_store_targets)
    except Exception as e:
        if type(e).__name__ == 'UnboundLocalError':
            print("=== UnboundLocalError in _generate_boolop ===")
            tb = e.__traceback__
            for fr in traceback.extract_tb(tb):
                print(f"  {fr.filename}:{fr.lineno} in {fr.name}: {fr.line[:80] if fr.line else ''}")
            print("=== end ===")
        raise


rag.RegionASTGenerator._generate_boolop = patched_gb

from pycdc import PycDecompiler
dec = PycDecompiler()
dec.load_file(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b6576_probe.pyc")
out = io.StringIO()
dec.decompile(out, use_region=True)
print("--- output tail (aug_boolop) ---")
src = out.getvalue()
idx = src.find('aug_boolop')
print(src[idx:idx + 120] if idx >= 0 else src[-300:])
