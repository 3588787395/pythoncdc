"""R17 调试：追踪 Expr→Return 转换发生的位置"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole


PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}

    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)

    walk(code_obj)
    return result


codes = load_pyc_code_objects(PYC)
f_code = codes['load_get_index_stocks']

cfg = build_cfg(f_code)

# 给 _if_generate_else_branch 打补丁
import core.cfg.region_ast_generator as rag_module

orig_else = rag_module.RegionASTGenerator._if_generate_else_branch
def traced_else(self, region):
    result = orig_else(self, region)
    # 检查是否含 Expr(Call data.sort)
    if result:
        for s in result:
            if isinstance(s, dict) and s.get('type') == 'Expr':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _if_generate_else_branch returned Expr(Call data.sort) !!!")
                        print(f"  Full result: {result}")
                        import traceback
                        traceback.print_stack()
            elif isinstance(s, dict) and s.get('type') == 'Return':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _if_generate_else_branch returned Return(Call data.sort) - BUG !!!")
                        print(f"  Full result: {result}")
    return result
rag_module.RegionASTGenerator._if_generate_else_branch = traced_else

# 给 _if_generate_then_branch 打补丁
orig_then = rag_module.RegionASTGenerator._if_generate_then_branch
def traced_then(self, region):
    result = orig_then(self, region)
    if result:
        for s in result:
            if isinstance(s, dict) and s.get('type') == 'Return':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _if_generate_then_branch returned Return(Call data.sort) - BUG !!!")
                        import traceback
                        traceback.print_stack()
    return result
rag_module.RegionASTGenerator._if_generate_then_branch = traced_then

# 给 _if_generate_normal 打补丁
orig_normal = rag_module.RegionASTGenerator._if_generate_normal
def traced_normal(self, region):
    result = orig_normal(self, region)
    if isinstance(result, dict):
        body = result.get('body', [])
        orelse = result.get('orelse', [])
        for s in body + orelse:
            if isinstance(s, dict) and s.get('type') == 'Return':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _if_generate_normal returned Return(Call data.sort) - BUG !!!")
                        print(f"  body: {body}")
                        print(f"  orelse: {orelse}")
                        import traceback
                        traceback.print_stack()
    return result
rag_module.RegionASTGenerator._if_generate_normal = traced_normal

# 给 _generate_if 打补丁
orig_gen_if = rag_module.RegionASTGenerator._generate_if
def traced_gen_if(self, region):
    result = orig_gen_if(self, region)
    if isinstance(result, dict):
        body = result.get('body', [])
        orelse = result.get('orelse', [])
        for s in body + orelse:
            if isinstance(s, dict) and s.get('type') == 'Return':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _generate_if returned Return(Call data.sort) - BUG !!!")
    elif isinstance(result, list):
        for s in result:
            if isinstance(s, dict) and s.get('type') == 'Return':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _generate_if (list) returned Return(Call data.sort) - BUG !!!")
    return result
rag_module.RegionASTGenerator._generate_if = traced_gen_if

# 给 _generate_loop 打补丁
orig_loop = rag_module.RegionASTGenerator._generate_loop
def traced_loop(self, region):
    result = orig_loop(self, region)
    if isinstance(result, list):
        for s in result:
            if isinstance(s, dict) and s.get('type') == 'Return':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _generate_loop (list) returned Return(Call data.sort) - BUG !!!")
                        import traceback
                        traceback.print_stack()
    return result
rag_module.RegionASTGenerator._generate_loop = traced_loop

# 给 _generate_region 打补丁
orig_gen_reg = rag_module.RegionASTGenerator._generate_region
def traced_gen_reg(self, region):
    result = orig_gen_reg(self, region)
    if isinstance(result, list):
        for s in result:
            if isinstance(s, dict) and s.get('type') == 'Return':
                v = s.get('value')
                if isinstance(v, dict) and v.get('type') == 'Call':
                    func = v.get('func')
                    if isinstance(func, dict) and func.get('attr') == 'sort':
                        print(f"\n!!! _generate_region (list) returned Return(Call data.sort) - BUG !!!")
                        rtype = type(region).__name__
                        print(f"  region type: {rtype}")
                        import traceback
                        traceback.print_stack()
    return result
rag_module.RegionASTGenerator._generate_region = traced_gen_reg

print("=== 生成 AST (with tracing) ===")
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
print("=== 完成 ===")
