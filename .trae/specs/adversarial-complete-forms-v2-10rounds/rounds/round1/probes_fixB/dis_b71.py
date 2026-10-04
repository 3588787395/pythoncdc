"""B71 诊断：dis r10_21 三函数字节码 + finally 块布局"""
import dis, sys, io

pyc = r"f:\Downloads\pythoncdc-main\test_repros\round10\r10_21_fin_loopctrl.pyc"
import importlib.util
spec = importlib.util.spec_from_file_location("r10_21", pyc)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

out = io.StringIO()
for name in ("fin_continue", "fin_break", "fin_continue_stmt"):
    fn = getattr(mod, name)
    out.write(f"\n{'='*70}\n### {name}\n{'='*70}\n")
    dis.dis(fn, file=out, show_caches=False)

with open(r"f:\Downloads\pythoncdc-main\.trae\specs\adversarial-complete-forms-v2-10rounds\rounds\round1\probes_fixB\b71_dis.txt", "w", encoding="utf-8") as f:
    f.write(out.getvalue())
print("written", len(out.getvalue()))
