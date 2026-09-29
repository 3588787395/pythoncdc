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

anchor = """            if len(_r37_reachable) < len(collected):
                collected = [b for b in collected if b in _r37_reachable]

        return collected
"""
assert u.count(anchor) == 1, u.count(anchor)
repl = """            if len(_r37_reachable) < len(collected):
                collected = [b for b in collected if b in _r37_reachable]

        # [R75 fix2 · edit-D2] 重定向承接的函数尾 return None 不属任何分支臂。
        # 识别条件（全结构事实）：收集块是无后继的纯隐式 `return None`
        # （LOAD_CONST None; RETURN_VALUE / RETURN_CONST None），且其唯一前驱的
        # 去噪指令恰为一条 JUMP_FORWARD——即该前驱不含任何语句，只是把控制流
        # 搬到尾部的中转。归约方式：从臂中移除，使其回归顶层序列，按地址序
        # 发射在 if/else 之后。AST 映射：分支体止于中转块之前，尾部 return
        # None 出现在 if 语句之后（4 空格）而非 if 体内（8 空格）。
        # 靶 IQCommon/util/trade_info_utils.pyc :: query_trade_strategy_info
        # （FOR_ITER 耗尽出口 478 → 尾 618：原把 618 收进 then 臂，产物把
        # `return None` 发射在 try 之内）。对称靶 query_strategy_id 的尾 648
        # 因经由 handler 出口本就不在臂内，故不受影响。
        # 仅在 merge is None（无界收集）时适用；有 merge 边界的收集已由
        # merge 终止，不受本规则触碰。
        if not merge and len(collected) > 1:
            _r75d2_in = set(collected)
            _r75d2_drop = set()
            for _r75d2_b in collected:
                if _r75d2_b is entry:
                    continue
                _r75d2_li = _r75d2_b.get_last_instruction()
                _r75d2_none = False
                if _r75d2_li is not None and _r75d2_li.opname == 'RETURN_CONST':
                    _r75d2_none = _r75d2_li.argval is None
                elif _r75d2_li is not None and _r75d2_li.opname == 'RETURN_VALUE':
                    _r75d2_prevs = [i for i in _r75d2_b.instructions
                                    if i.offset < _r75d2_li.offset
                                    and i.opname not in ('NOP', 'CACHE',
                                                         'EXTENDED_ARG', 'RESUME')]
                    _r75d2_none = (bool(_r75d2_prevs)
                                   and _r75d2_prevs[-1].opname == 'LOAD_CONST'
                                   and _r75d2_prevs[-1].argval is None)
                if not _r75d2_none:
                    continue
                _r75d2_preds = [p for p in (_r75d2_b.predecessors or [])
                                if p in _r75d2_in]
                if len(_r75d2_preds) != 1:
                    continue
                _r75d2_p = _r75d2_preds[0]
                _r75d2_pops = [i.opname for i in _r75d2_p.instructions
                               if i.opname not in ('NOP', 'CACHE', 'EXTENDED_ARG',
                                                   'RESUME', 'PUSH_NULL')]
                if _r75d2_pops == ['JUMP_FORWARD']:
                    _r75d2_drop.add(_r75d2_b)
            if _r75d2_drop:
                collected = [b for b in collected if b not in _r75d2_drop]

        return collected
"""

spec = {"file": "core/cfg/region_analyzer.py", "edits": [{"anchor": anchor, "repl": repl}]}
json.dump(spec, io.open(os.path.join(D, "editd5.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

ad4 = json.load(io.open(os.path.join(D, "ad4.json"), encoding="utf-8"))
merged = {"file": "core/cfg/region_analyzer.py",
          "edits": list(ad4["edits"]) + list(spec["edits"])}
mpath = os.path.join(D, "ad5.json")
json.dump(merged, io.open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", mpath, "edits", len(merged["edits"]))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5 %s %s"
        % (G, os.path.join(D, "ec_g.json"), mpath))
print(r.stdout, r.stderr)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5 "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s\\fix2\\dump\\d5.txt %s\\fix2\\dump\\ecafgd5_tiu.py" % (G, G, G))
print(r.stdout)
r = run("python -W ignore -X utf8 F:\\Downloads\\pythoncdc-main\\scripts\\pyc_verify.py single "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "--source %s\\fix2\\dump\\ecafgd5_tiu.py" % G)
print(r.stdout, r.stderr)
