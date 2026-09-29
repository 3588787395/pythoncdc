import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = r"F:\Downloads\pythoncdc-main"
D = r"D:\Temp\opencode\r75gate\fix2\specs"
G = r"D:\Temp\opencode\r75gate"
path = os.path.join(REPO, "core", "cfg", "region_ast_generator.py")
src = io.open(path, encoding="utf-8-sig", newline="").read()
nl = "\r\n" if "\r\n" in src else "\n"
u = src.replace(nl, "\n")

# ---- E1: pull the for-loop exhaustion break stub into the try body block list ----
anchor1 = """                    _inlined_ret_offsets.add(_succ.start_offset)
        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):
"""
assert u.count(anchor1) == 1, u.count(anchor1)
repl1 = """                    _inlined_ret_offsets.add(_succ.start_offset)

        # [R75 fix2 · edit-E1] for 循环耗尽出口的 break 桩归入 try 体块表。
        # 识别条件（全结构事实）：候选块是本 try 有效体块末指令为 FOR_ITER
        # （循环耗尽边）的后继，偏移落在 [try_offset_start, 首个 handler) 的
        # 间隙内，且区域分析器给它的角色是 BREAK/PURE_BREAK（该角色由
        # 「候选块越出所属 LoopRegion」推得，不读名字与绝对偏移）。
        # 归约依据——CPython 异常表只覆盖可抛出指令，try 体内不可抛出的
        # `break` 被移出 [try_start, try_end)，分析器的分支体扩展只认
        # CONDITIONAL_JUMP 前驱，故该桩既不在 region.try_blocks 也不在
        # region.blocks；try 体主循环按 region.blocks 找嵌套区域，命中「嵌套
        # 区域已生成」分支后因 `block in region.try_blocks` 为假而只标记不发射，
        # try 体末尾的 `break` 永不产出（靶 get_trade_status 缺 break）。
        # AST 映射——追加进 _try_blocks_eff 后按偏移排序位于 try 体之末，
        # 与 _generate_block_statements 的 BLOCK 角色分支产出
        # [{'type': 'Break'}] 对齐；_r75e_pulled 记录本次新拉入的块，供
        # [R75 fix2 · edit-E2] 在嵌套区域分支里放行发射。
        # 靶 IQCommon/util/trade_info_utils.pyc :: get_trade_status
        # （456 FOR_ITER 耗尽 → 598 JUMP_FORWARD 810，598 = try_end）。
        _r75e_pulled = set()
        if _try_blocks_eff and _handler_block_offsets:
            _r75e_hmin = min(_handler_block_offsets)
            for _tb in list(_try_blocks_eff):
                _tb_last = _tb.get_last_instruction()
                if _tb_last is None or 'FOR_ITER' not in _tb_last.opname:
                    continue
                for _succ in _tb.successors:
                    if _succ.start_offset in _already_in_eff:
                        continue
                    if _succ.start_offset in _handler_block_offsets:
                        continue
                    if region.try_offset_start is None:
                        continue
                    if not (region.try_offset_start <= _succ.start_offset < _r75e_hmin):
                        continue
                    _r75e_role = self.region_analyzer.get_block_role(_succ)
                    if _r75e_role not in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                        continue
                    _try_blocks_eff.append(_succ)
                    _already_in_eff.add(_succ.start_offset)
                    _r75e_pulled.add(_succ.start_offset)
        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):
"""

# ---- E2: let the nested-region branch emit the pulled-in break stub ----
anchor2 = """                nested_id = id(nested_region)
                if nested_id in self._generated_regions or nested_id in self._generating_regions:
                    if block in region.try_blocks:
                        stmts = self._generate_block_statements(block)
                        body_stmts.extend(stmts)
                    self.generated_blocks.add(block)
                    continue
"""
assert u.count(anchor2) == 1, u.count(anchor2)
repl2 = """                nested_id = id(nested_region)
                if nested_id in self._generated_regions or nested_id in self._generating_regions:
                    # [R75 fix2 · edit-E2] 嵌套区域（如外层 while/内层 for）已生成
                    # 或正在生成时，原判据 `block in region.try_blocks` 会把
                    # 「分析器因异常表区间而排除出 try_blocks」的 break 桩
                    # （见 [R75 fix2 · edit-E1]）标记却不发射，try 体末尾的
                    # `break` 丢失。放行 edit-E1 拉入的块：它们本就属
                    # _try_blocks_eff，语句须进 try 体。
                    if block in region.try_blocks or block.start_offset in _r75e_pulled:
                        stmts = self._generate_block_statements(block)
                        body_stmts.extend(stmts)
                    self.generated_blocks.add(block)
                    continue
"""

spec = {"file": "core/cfg/region_ast_generator.py",
        "edits": [{"anchor": anchor1, "repl": repl1},
                  {"anchor": anchor2, "repl": repl2}]}
json.dump(spec, io.open(os.path.join(D, "ede.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

ecg = json.load(io.open(os.path.join(D, "ec_g.json"), encoding="utf-8"))
merged = {"file": "core/cfg/region_ast_generator.py",
          "edits": list(ecg["edits"]) + list(spec["edits"])}
mpath = os.path.join(D, "ec_ge.json")
json.dump(merged, io.open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", mpath, "edits", len(merged["edits"]))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5e %s %s"
        % (G, mpath, os.path.join(D, "ad5.json")))
print(r.stdout, r.stderr)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5e "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s\\fix2\\dump\\e.txt %s\\fix2\\dump\\ecafgd5e_tiu.py" % (G, G, G))
print(r.stdout, r.stderr)
r = run("python -W ignore -X utf8 F:\\Downloads\\pythoncdc-main\\scripts\\pyc_verify.py single "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "--source %s\\fix2\\dump\\ecafgd5e_tiu.py" % G)
print(r.stdout, r.stderr)
