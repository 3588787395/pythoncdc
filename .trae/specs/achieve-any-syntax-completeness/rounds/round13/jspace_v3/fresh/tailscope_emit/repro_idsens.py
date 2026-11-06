# rr-v5r126 最小复现：同进程两次反编译（id 布局漂移）输出翻转探测
import sys, os
REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = 'F:/Downloads/pythoncdc-main/.trae/specs/attack-completeness-claims/rounds/round6/offcorpus/stdlib_xml_ElementPath.pyc'

def decompile_fn(pyc, fn_name):
    module = load_pyc_file_v2(pyc)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    root = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
    def find_code(code, acc):
        for c in code.co_consts:
            if hasattr(c, 'co_name'):
                acc.append(c); find_code(c, acc)
    acc = []
    find_code(root, acc)
    fn = [c for c in acc if c.co_name == fn_name][0]
    cfg = build_cfg(fn)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    gen.generate()
    # 产线文本化：用现有转换+代码生成太重，直接比区域树签名（entry/blocks/children）
    sig = []
    for r in gen.regions:
        tn = type(r).__name__
        par = getattr(r, 'parent', None)
        kids = tuple(sorted(k.entry.start_offset for k in (getattr(r, 'children', None) or [])))
        sig.append((tn, r.entry.start_offset,
                    tuple(sorted(b.start_offset for b in r.blocks)),
                    par.entry.start_offset if par is not None else None, kids))
    return sorted(sig)

# run1
sig1 = decompile_fn(PYC, 'iterfind')
# id 布局扰动：分配并释放一批对象，再跑
noise = [[{'x': i} for i in range(200)] for _ in range(50)]
del noise
# run2
sig2 = decompile_fn(PYC, 'iterfind')
# run3
sig3 = decompile_fn(PYC, 'iterfind')

print('run1 == run2:', sig1 == sig2)
print('run2 == run3:', sig2 == sig3)
if sig1 != sig2:
    s1, s2 = set(sig1), set(sig2)
    print('only-run1:', sorted(s1 - s2)[:4])
    print('only-run2:', sorted(s2 - s1)[:4])
