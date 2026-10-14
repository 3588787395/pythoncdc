"""gate_r108.py - read-only: which gate rejects each target block?"""
import sys
sys.path.insert(0, ".")
import core.cfg.region_ast_generator as RAG

PYC = ("D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/"
       "plugins/plugin_system_event_source/realtime_event_source.pyc")
LO, HI = 7900, 8700
LOG = []


def o(x):
    return getattr(x, "start_offset", x)


G = RAG.RegionASTGenerator


def in_clock(self):
    return getattr(self.cfg, "name", "") == "clock_worker"


d_dispatch = G._loop_dispatch_block
d_child = G._loop_handle_child_region_entry
d_blockstmt = G._generate_block_statements
d_loop = G._generate_loop


def w_dispatch(self, block, region, *a, **kw):
    off = o(block)
    rec = None
    if in_clock(self) and LO <= off <= HI:
        er = self.region_analyzer.get_entry_region_for_block(block)
        br = self.region_analyzer.get_region_for_block(block)
        rec = ["dispatch", off,
               "loop@" + str(o(region.entry)),
               "role=" + str(self.region_analyzer.get_block_role(block)),
               "gen=" + str(block in self.generated_blocks),
               "entryreg=" + (type(er).__name__ + "@" + str(o(er.entry)) if er is not None and er.entry is not None else "None"),
               "blkreg=" + (type(br).__name__ + "@" + str(o(br.entry)) if br is not None and br.entry is not None else "None"),
               "is_dchild=" + str(any(c.entry is block for c in (region.children or ())))]
    r = d_dispatch(self, block, region, *a, **kw)
    if rec is not None:
        rec.append("handled=" + str(r))
        LOG.append(rec)
    return r


def w_child(self, block, region, child_info, body_stmts):
    off = o(block)
    r = d_child(self, block, region, child_info, body_stmts)
    if in_clock(self) and LO <= off <= HI:
        LOG.append(["child_entry", off, "returned=" + str(r)])
    return r


def w_stmt(self, block, *a, **kw):
    off = o(block)
    if in_clock(self) and LO <= off <= HI:
        LOG.append(["stmt", off])
    return d_blockstmt(self, block, *a, **kw)


def w_loop(self, region, *a, **kw):
    if in_clock(self):
        LOG.append(["LOOP", o(region.entry), "nbody=" + str(len(region.body_blocks or ()))])
    return d_loop(self, region, *a, **kw)


G._loop_dispatch_block = w_dispatch
G._loop_handle_child_region_entry = w_child
G._generate_block_statements = w_stmt
G._generate_loop = w_loop

from pycdc import decompile_pyc
decompile_pyc(PYC)

seen = {}
for rec in LOG:
    if rec[0] in ("dispatch", "child_entry", "stmt"):
        seen.setdefault(rec[1], []).append(rec)

print("=== LOOP visits ===")
for rec in LOG:
    if rec[0] == "LOOP":
        print(rec)

print("=== per-block gate trace ===")
for off in sorted(seen):
    print("@" + str(off))
    for rec in seen[off]:
        print("     " + " | ".join(str(x) for x in rec))

CENSUS = [7972, 7980, 8166, 8170, 8184, 8186, 8256, 8258, 8276, 8282, 8286, 8288,
          8294, 8306, 8350, 8354, 8400, 8450, 8504, 8544, 8548, 8588, 8592]
print("=== census blocks never touched ===")
print([x for x in CENSUS if x not in seen])
