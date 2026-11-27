# Or-pattern shape probe: does `case [] | [0]:` produce LOAD_FAST+COPY (v2
# match detection) and does the REGION phase avoid the 2190/2251 trap?
import dis
import os
import sys

SRC = "def f(x):\n    match x:\n        case [] | [0]:\n            return 1\n    return -1\n"
c = compile(SRC, '<orpat>', 'exec')
print('--- dis of f ---')
dis.dis(c.co_consts[0])

ROOT = r'F:\Downloads\pythoncdc-main'
os.chdir(ROOT)
sys.path.insert(0, ROOT)
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
from core.cfg.ast_generator_v2 import generate_ast_v2

AGV2 = 'ast_generator_v2.py'
PP = 'pattern_parser.py'
SA = 'structured_analyzer.py'
ANCHORS = {(AGV2, 21513): 'agv2.21513', (AGV2, 21525): 'agv2.21525',
           (AGV2, 21641): 'agv2.21641', (PP, 2190): 'pp.2190',
           (PP, 2251): 'pp.2251', (PP, 2452): 'pp.2452'}
log = []


def tr(frame, event, arg):
    if event == 'call' and os.path.basename(frame.f_code.co_filename) == SA:
        name = frame.f_code.co_name
        if name in ('_find_match_subject', '_analyze_match_structure',
                    '_extract_match_pattern', '_identify_match_structures'):
            log.append('CALL %s' % name)
        return tr
    if event == 'line':
        key = ANCHORS.get((os.path.basename(frame.f_code.co_filename), frame.f_lineno))
        if key:
            instr = frame.f_locals.get('instr')
            log.append('%s %s' % (key, getattr(instr, 'opname', '<no-instr>')))
    return tr


sys.settrace(tr)
try:
    cfg = build_cfg(c)
    ast_dict = RegionASTGenerator(cfg, top_level_code=c).generate()
    out = CFGCodeGenerator().generate(CFGASTConverter().convert(ast_dict))
except BaseException as e:
    out = 'REGION FAIL %s: %s' % (type(e).__name__, e)
finally:
    sys.settrace(None)
print('--- region out ---')
print(out)
print('--- region events ---')
for line in log:
    print('    ' + line)
if not log:
    print('    (none)')

log.clear()
sys.settrace(tr)
try:
    ast_dict_v2 = generate_ast_v2(build_cfg(c))
    out2 = CFGCodeGenerator().generate(CFGASTConverter().convert(ast_dict_v2))
except BaseException as e:
    out2 = 'V2 FAIL %s: %s' % (type(e).__name__, e)
finally:
    sys.settrace(None)
print('--- v2 out ---')
print(out2)
print('--- v2 events ---')
for line in log:
    print('    ' + line)
if not log:
    print('    (none)')
