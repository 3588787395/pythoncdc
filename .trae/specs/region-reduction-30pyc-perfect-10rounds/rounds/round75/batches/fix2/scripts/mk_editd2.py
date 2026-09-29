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

# 1) init the crossing flag right after the loop header
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
        # [R75 fix2 · edit-D] 跨语句标记：清理扫描一旦越过一块含用户代码的块，
        # 其后的候选就不再与 with 出口连续（本方法上方注释已声明「WITH 清理区是
        # 连续的」）。
        _r75d_crossed = False
        for block in self.cfg.get_blocks_in_order():
"""

# 2) set the flag instead of continuing blindly, and release a terminal
#    trailing return-none that lies beyond the crossing point
anchor2 = """            if has_user_code:
                continue
"""
assert u.count(anchor2) == 1, u.count(anchor2)
repl2 = """            if has_user_code:
                # [R75 fix2 · edit-D] 记录「已跨过真实语句」；清理扫描按地址序前进，
                # 跨过用户语句后仍会继续吃块（continue 不 break），因此后续必须
                # 对「跨点之后的纯隐式 return None 尾块」让位，否则它会被 WithRegion
                # 唯一认领并发射在 with 之后、外层 if 之内（位置错位）。
                # 靶 IQCommon/util/trade_info_utils.pyc :: query_strategy_id（with 在
                # if-then 内，函数尾 @648 在外层 if/else 之后）与
                # query_trade_strategy_info（尾 @618）：扫描先跳过
                # `trade_df = df[...]` 等用户语句，再吃到 @644/@648。
                # 判据只读「块内是否含用户代码指令类别」+「块是否为无后继的纯
                # LOAD_CONST None; RETURN_VALUE / RETURN_CONST None 终止块」两条结构
                # 事实，不看函数名/文件名/偏移阈值/名字白名单。
                _r75d_crossed = True
                continue
            if _r75d_crossed and not block.successors:
                _r75d_ins = [i for i in block.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                _r75d_ops = [i.opname for i in _r75d_ins]
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
                if _r75d_none:
                    continue
"""

spec = {"file": "core/cfg/region_analyzer.py",
        "edits": [{"anchor": anchor1, "repl": repl1},
                  {"anchor": anchor2, "repl": repl2}]}
out = os.path.join(D, "editd2.json")
json.dump(spec, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out)

pad = json.load(io.open(os.path.join(D, "pad8_1f.json"), encoding="utf-8"))
merged = {"file": "core/cfg/region_analyzer.py",
          "edits": list(spec["edits"]) + list(pad["edits"])}
mpath = os.path.join(D, "ad2.json")
json.dump(merged, io.open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", mpath, "edits", len(merged["edits"]))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd2 %s %s"
        % (G, os.path.join(D, "ec_g.json"), mpath))
print(r.stdout, r.stderr)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd2 "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s\\fix2\\dump\\ecafgd2_tiu.py" % (G, G))
print(r.stdout)
r = run("python -W ignore -X utf8 F:\\Downloads\\pythoncdc-main\\scripts\\pyc_verify.py single "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "--source %s\\fix2\\dump\\ecafgd2_tiu.py" % G)
print(r.stdout)
