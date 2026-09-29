import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = r"F:\Downloads\pythoncdc-main"
D = r"D:\Temp\opencode\r75gate\fix2\specs"
G = r"D:\Temp\opencode\r75gate"
path = os.path.join(REPO, "core", "cfg", "region_analyzer.py")
src = io.open(path, encoding="utf-8-sig", newline="").read()
nl = "\r\n" if "\r\n" in src else "\n"
u = src.replace(nl, "\n")

anchor1 = """    def _collect_normal_exit_cleanup(self, with_body, cleanup, cleanup_visited,
                                    entry_blocks, body_end):
        body_offsets = {b.start_offset for b in with_body}
        body_offsets.update(b.start_offset for b in entry_blocks)
        for block in self.cfg.get_blocks_in_order():
"""
assert u.count(anchor1) == 1, u.count(anchor1)
repl1 = """    def _collect_normal_exit_cleanup(self, with_body, cleanup, cleanup_visited,
                                    entry_blocks, body_end):
        body_offsets = {b.start_offset for b in with_body}
        body_offsets.update(b.start_offset for b in entry_blocks)
        # [R75 fix2 · edit-D] 跨语句标记：本方法上方注释已声明「WITH 清理区是连续
        # 的，终止于 WITH 块的自然出口」。扫描按地址序前进且遇到含用户代码的块只
        # continue 不 break，因此会跨过真实语句继续吃块。
        _r75d_crossed = False
        for block in self.cfg.get_blocks_in_order():
"""

anchor2 = """            if has_user_code:
                continue
"""
assert u.count(anchor2) == 1, u.count(anchor2)
repl2 = """            if has_user_code:
                # [R75 fix2 · edit-D] 记录「已跨过真实语句」。
                _r75d_crossed = True
                continue
            # [R75 fix2 · edit-D] （1）纯跳转占位块：块内去掉噪声后只有一条
            # JUMP_FORWARD——它不含 __exit__ 调用，也不是栈回卷路径，只是把控制流
            # 搬到别处的中转（靶 query_trade_strategy_info 中 except handler 出口
            # 478 → 函数尾 618）。把它算作 with 的正常清理会让 WithRegion 的块区间
            # 越过随后的 for 循环，把 for 误吞进 with 体内。
            _r75d_ins = [i for i in block.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            _r75d_ops = [i.opname for i in _r75d_ins]
            if _r75d_ops == ['JUMP_FORWARD']:
                continue
            # [R75 fix2 · edit-D] （2）跨点之后、由 except handler 出口跳入的纯隐式
            # `return None` 终止块：它不是 with 的清理路径，而是外层 try/except +
            # if/else 之后的**函数级**尾语句。若被 WithRegion 唯一认领，会被发射在
            # with 之后（即 if 体内 try 之后），位置错位。
            # 靶 query_strategy_id（尾 @648，前驱 @466 = POP_EXCEPT + JUMP_FORWARD）
            # 与 query_trade_strategy_info（尾 @618，前驱 @478 同形）。
            # 判据全为结构事实，无函数名/文件名/偏移阈值/名字白名单：
            #   ① 已跨过含用户代码的块；② 本块无后继；
            #   ③ 块内恰为 `LOAD_CONST None; RETURN_VALUE` 或 `RETURN_CONST None`；
            #   ④ 存在前驱且每条前驱的末指令均为 JUMP_FORWARD（handler 出口跳）。
            if _r75d_crossed and not block.successors:
                _r75d_none = False
                if _r75d_ops:
                    if (_r75d_ops[-1] == 'RETURN_CONST'
                            and _r75d_ins[-1].argval is None):
                        _r75d_none = True
                    elif (len(_r75d_ops) >= 2
                          and _r75d_ops[-1] == 'RETURN_VALUE'
                          and _r75d_ops[-2] == 'LOAD_CONST'
                          and _r75d_ins[-2].argval is None):
                        _r75d_none = True
                _r75d_preds = list(block.predecessors or [])
                if (_r75d_none and _r75d_preds and all(
                        p.instructions and p.get_last_instruction().opname == 'JUMP_FORWARD'
                        for p in _r75d_preds)):
                    continue
"""

spec = {"file": "core/cfg/region_analyzer.py",
        "edits": [{"anchor": anchor1, "repl": repl1},
                  {"anchor": anchor2, "repl": repl2}]}
out = os.path.join(D, "editd4.json")
json.dump(spec, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out)

pad = json.load(io.open(os.path.join(D, "pad8_1f.json"), encoding="utf-8"))
merged = {"file": "core/cfg/region_analyzer.py",
          "edits": list(spec["edits"]) + list(pad["edits"])}
mpath = os.path.join(D, "ad4.json")
json.dump(merged, io.open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", mpath, "edits", len(merged["edits"]))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd4 %s %s"
        % (G, os.path.join(D, "ec_g.json"), mpath))
print(r.stdout, r.stderr)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd4 "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s\\fix2\\dump\\d4.txt %s\\fix2\\dump\\ecafgd4_tiu.py" % (G, G, G))
print(r.stdout)
r = run("python -W ignore -X utf8 F:\\Downloads\\pythoncdc-main\\scripts\\pyc_verify.py single "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "--source %s\\fix2\\dump\\ecafgd4_tiu.py" % G)
print(r.stdout, r.stderr)
