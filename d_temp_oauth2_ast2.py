import sys, types, io, json
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(co, name, parent_name=None):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                if parent_name is None or co.co_name == parent_name:
                    return c
            r = find_code(c, name, parent_name)
            if r: return r
    return None

co = find_code(code, 'post', 'OAuthCallbackHandler')
builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, regions, analyzer)
ast_result = ast_gen.generate()

# Just print the full AST result
def show(d, depth=0):
    if isinstance(d, dict):
        t = d.get('type', '?')
        if depth > 2:
            return f"{t}(...)"
        keys_to_show = ['type', 'name', 'id', 'attr', 'op', 'value']
        result = {}
        for k in keys_to_show:
            if k in d:
                v = d[k]
                if k == 'value' and isinstance(v, dict) and depth >= 1:
                    result[k] = show(v, depth+1)
                elif k == 'value' and isinstance(v, list) and depth >= 1:
                    result[k] = [show(x, depth+1) for x in v[:3]]
                    if len(v) > 3:
                        result[k].append('...')
                else:
                    result[k] = v
        if 'body' in d:
            b = d['body']
            if isinstance(b, list):
                result['body'] = [show(x, depth+1) for x in b[:5]]
                if len(b) > 5:
                    result['body'].append(f'...({len(b)} total)')
        if 'orelse' in d:
            o = d['orelse']
            if isinstance(o, list):
                result['orelse'] = [show(x, depth+1) for x in o[:3]]
                if len(o) > 3:
                    result['orelse'].append('...')
        if 'test' in d:
            result['test'] = show(d['test'], depth+1)
        if 'targets' in d:
            result['targets'] = [show(x, depth+1) for x in d['targets'][:2]]
        return result
    if isinstance(d, list):
        return [show(x, depth+1) for x in d[:10]]
    return d

print(json.dumps(show(ast_result), indent=2, default=str))
