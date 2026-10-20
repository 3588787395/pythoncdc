import io
import marshal
import sys
import types

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

target = sys.argv[1] if len(sys.argv) > 1 else "mA"
pyc = sys.argv[2] if len(sys.argv) > 2 else "test_repros/round5/_r5min1.pyc"
data = open(pyc, "rb").read()
code = marshal.loads(data[16:])


def find(code, name, out):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if name in c.co_qualname or name in c.co_name:
                out.append(c)
            find(c, name, out)


co_list = []
find(code, target, co_list)
co = co_list[-1]
print("=== disassembly", co.co_qualname, "===")
import dis
for ins in dis.get_instructions(co):
    print("%5d %-28s %r" % (ins.offset, ins.opname, ins.argval))

cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
pp = gen.region_analyzer.pattern_parser
orig = pp.parse_case_guard


def traced(pb, allow_in_header_block=False, fail_case_offset=None):
    print("\n=== parse_case_guard call ===")
    print("blocks:", [b.start_offset for b in pb])
    print("allow_in_header:", allow_in_header_block, "fail_off:", fail_case_offset)
    for b in pb:
        eff = [(i.opname, i.argval) for i in b.instructions
               if i.opname not in ("RESUME", "NOP", "CACHE", "PUSH_NULL")]
        print("  block@%s: %s" % (b.start_offset, eff))
    r = orig(pb, allow_in_header_block, fail_case_offset)
    print("  => guard:", r)
    return r


pp.parse_case_guard = traced
regions = gen.region_analyzer.analyze()
print("\n=== regions ===")
for r in regions:
    t = type(r).__name__
    print(t, "entry", getattr(r.entry, "start_offset", None))
    if t == "MatchRegion":
        print("  case_blocks:", [b.start_offset for b in r.case_blocks])
        print("  case_guards:", r.case_guards)
        print("  case_patterns:", r.case_patterns)
        print("  case_bodies:", [[b.start_offset for b in body] for body in r.case_bodies])
