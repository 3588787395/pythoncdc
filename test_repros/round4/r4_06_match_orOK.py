# Source Generated with Decompyle++ (Python version)
# File: r4_06_match_or.pyc (Python 3.11)

def match_or_values(x):
    """Attack 1: or-pattern over literal values."""
    match x:
        case 1 | 2 | 3:
            return 'small'
        case 4 | 5:
            return 'mid'
        case _:
            return 'big'
def match_or_str(x):
    """Attack 2: or-pattern over strings."""
    match x:
        case 'yes' | 'y' | 'ok':
            return True
        case 'no' | 'n':
            return False
        case _:
            pass
def match_or_sequence(seq):
    """Attack 3: or-pattern over sequence shapes."""
    match seq:
        case {'type': 'MatchSequence', 'patterns': [<core.ast_nodes.ASTConstant object at 0x0000019526368D10>, <core.ast_nodes.ASTConstant object at 0x0000019526369350>], 'as_name': None} | {'type': 'MatchSequence', 'patterns': [<core.ast_nodes.ASTConstant object at 0x0000019526368E00>, <core.ast_nodes.ASTConstant object at 0x00000195263690D0>], 'as_name': None}:
            return 'diagonal'
        case {'type': 'MatchSequence', 'patterns': [<core.ast_nodes.ASTConstant object at 0x0000019526368810>, <core.ast_nodes.ASTName object at 0x0000019528469D20>], 'as_name': None} | {'type': 'MatchSequence', 'patterns': [<core.ast_nodes.ASTName object at 0x0000019528469DE0>, <core.ast_nodes.ASTConstant object at 0x00000195263687C0>], 'as_name': None}:
            return ('axis', y)
        case _:
            return 'elsewhere'
def match_or_mixed_types(x):
    """Attack 4: or-pattern mixing int and str."""
    match x:
        case 0 | 'zero':
            return 0
        case 1 | 'one':
            return 1
        case _:
            return -1
def match_or_capture_body(x):
    """Attack 5: or-pattern combined with guard and body work."""
    match x:
        case 1 | 2 | 3 | 4:
            for i in range(x):
                total.append(i)
            return total
        case 5 | 6:
            total.append(x * 10)
        case _:
            total = None
