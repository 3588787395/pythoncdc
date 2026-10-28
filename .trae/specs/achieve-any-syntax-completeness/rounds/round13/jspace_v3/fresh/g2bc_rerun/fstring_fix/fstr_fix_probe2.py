# Round13 probe 2: AST path (production pipeline) precise verification.
import sys
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.code_generator import CFGCodeGenerator
from core.ast_nodes import (ASTJoinedStr, ASTFormattedValue, ASTConstant,
                            ASTName, ASTAttribute, ASTCall)

gen = CFGCodeGenerator()

def show(tag, node):
    src = gen._generate_joined_str(node)
    print(f'--- {tag}')
    print('SRC_ASCII:', ascii(src))
    try:
        compile(src, '<probe>', 'eval')
        print('  COMPILE_OK')
    except SyntaxError as e:
        print(f'  SYNTAX_FAIL: {e}')

# A1: REAL46-004 exact shape (AST path): expr = '''<realNL>      '''.join(failed_member)
# converter renders Constant with real newline as triple-quoted (per _generate_constant)
fv1 = ASTFormattedValue(ASTName('name'), 0, None)
lit1 = ASTConstant(' member mismatch:\n      ')
c = ASTConstant('\n      ')
join_attr = ASTAttribute(c, 'join', 0)
call = ASTCall(join_attr, [ASTName('failed_member')], [])
fv2 = ASTFormattedValue(call, 1, None)  # !s
node1 = ASTJoinedStr([fv1, lit1, fv2])
show('A1 REAL46-004 shape (newline in expr, AST path)', node1)

# A2: expr with single-quote string only -> double delim
fv3 = ASTFormattedValue(ASTConstant("x != 'tick'"), 0, None)
show('A2 plain expr', ASTJoinedStr([ASTConstant('v='), fv3]))

# A3: expr with both quote kinds and newline -> should pick triple delim
fv4 = ASTFormattedValue(ASTConstant("a'b\nc\"d"), 0, None)
show('A3 both quotes + newline', ASTJoinedStr([fv4]))

# A4: expr with literal backslash -> Tier 2
fv5 = ASTFormattedValue(ASTConstant('a\\b'), 0, None)
show('A4 backslash -> Tier2', ASTJoinedStr([ASTConstant('p='), fv5, ASTConstant('!')]))

# A5: format spec as str (converter path) with newline in expr
fv6 = ASTFormattedValue(ASTConstant('line1\nline2'), 0, '>20')
show('A5 spec str + newline in expr', ASTJoinedStr([ASTConstant('s='), fv6]))

# A6: eval A1 semantically (needs name / failed_member in ns)
ns = {'name': 'SPAM', 'failed_member': ['m1', 'm2']}
print('A1_EVAL:', repr(eval(gen._generate_joined_str(node1), ns)))
