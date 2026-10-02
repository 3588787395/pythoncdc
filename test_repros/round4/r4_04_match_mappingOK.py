# Source Generated with Decompyle++ (Python version)
# File: r4_04_match_mapping.pyc (Python 3.11)

def match_map_basic(d):
    """Attack 1: basic mapping pattern with two keys."""
    match d:
        case {'name': n, 'age': a}:
            return (n, a)
def match_map_rest(d):
    """Attack 2: mapping with **rest capture."""
    match d:
        case {'type': rest}:
            return (t, sorted(rest.keys()))
def match_map_nested(d):
    """Attack 3: nested mapping pattern."""
    match d:
        case {'user': 2}:
            r, *others = None
            return (n, r, len(others))
        case {'user': 1}:
            return (n, 'noroles', 0)
def match_map_literal_values(d):
    """Attack 4: mapping with literal value constraints."""
    match d:
        case {'status': 'ok', 'code': 200}:
            return 'ok200'
        case {'status': 'err'}:
            return 'err'
        case {'status': s}:
            return ('status', s)
def match_map_mixed_seq(d):
    """Attack 5: mapping + sequence hybrid pattern."""
    match d:
        case {'points': {'type': 'MatchSequence', 'patterns': [{'type': 'MatchSequence', 'patterns': [<core.ast_nodes.ASTName object at 0x000001778941F640>, <core.ast_nodes.ASTName object at 0x000001778941F700>, <core.ast_nodes.ASTName object at 0x000001778941F7C0>, <core.ast_nodes.ASTName object at 0x000001778941F880>], 'as_name': 'y1'}, <core.ast_nodes.ASTName object at 0x000001778941F940>], 'as_name': None}}:
            return ((x1, y1), (x2, y2))
        case {'points': {'type': 'MatchSequence', 'patterns': [], 'as_name': None}}:
            return ()
