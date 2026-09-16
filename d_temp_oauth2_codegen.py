import sys, types, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_node import *
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

# Convert AST dict to AST nodes and generate code
code_gen = CodeGenerator()
output = io.StringIO()
code_gen.output = output
code_gen.indent_level = 0

# Try generating the entire function
if isinstance(ast_result, dict):
    ast_result = [ast_result]

from core.cfg.ast_node import ASTNode, ASTBlock
nodes = ASTBlock()
for item in ast_result:
    node = ASTNode.from_dict(item) if isinstance(item, dict) else item
    nodes.add_node(node)

code_gen._generate_block(nodes)
result = output.getvalue()
print(result)
