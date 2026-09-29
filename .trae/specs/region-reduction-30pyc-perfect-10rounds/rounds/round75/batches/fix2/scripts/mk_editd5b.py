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

        # [R75 fix2 · edit-D2'] 重定向承接的函数尾 return None 不属任何分支臂。
        # 识别条件（全结构事实）：收集块除隐式 return 序列外**不含任何语句**
        # （记号序列恰为 `LOAD_CONST None; RETURN_VALUE` 或 `RETURN_CONST None`，
        # 忽略 NOP/CACHE/EXTENDED_ARG/RESUME/PUSH_NULL），且其唯一前驱的
        # 去噪指令恰为一条 JUMP_FORWARD——即该前驱不含任何语句，只是把控制流
        # 搬到尾部的中转。纯度检查是必需的：`load` 类块形如
        # `del x; f(); LOAD_CONST None; RETURN_VALUE`，其末指令同为隐式 return，
        # 若不查纯度会把含用户语句的整块剔出臂外，导致语句外提（回归
        # IQCommon/data/asset_storage.pyc :: load）。
        # 归约方式：从臂中移除，使其回归顶层序列，按地址序发射在 if/else 之后。
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
                _r75d2_meaning = [i for i in _r75d2_b.instructions
                                  if i.opname not in ('NOP', 'CACHE',
                                                      'EXTENDED_ARG', 'RESUME',
                                                      'PUSH_NULL')]
                if not _r75d2_meaning:
                    continue
                _r75d2_li = _r75d2_meaning[-1]
                _r75d2_pure = False
                if _r75d2_li.opname == 'RETURN_CONST':
                    _r75d2_pure = (_r75d2_li.argval is None
                                   and len(_r75d2_meaning) == 1)
                elif _r75d2_li.opname == 'RETURN_VALUE':
                    _r75d2_pure = (len(_r75d2_meaning) == 2
                                   and _r75d2_meaning[0].opname == 'LOAD_CONST'
                                   and _r75d2_meaning[0].argval is None)
                if not _r75d2_pure:
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
json.dump(spec, io.open(os.path.join(D, "editd5b.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

ad4 = json.load(io.open(os.path.join(D, "ad4.json"), encoding="utf-8"))
merged = {"file": "core/cfg/region_analyzer.py",
          "edits": list(ad4["edits"]) + list(spec["edits"])}
mpath = os.path.join(D, "ad5b.json")
json.dump(merged, io.open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", mpath, "edits", len(merged["edits"]))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5b %s %s"
        % (G, os.path.join(D, "ec_ge.json"), mpath))
print((r.stdout or "").strip(), (r.stderr or "").strip()[:300])

lst = os.path.join(G, "center", "dump", "list41.txt")
out = os.path.join(G, "fix2", "dump", "list41_ecafd5b.jsonl")
r = run("python -W ignore -X utf8 %s\\center\\h62.py run --arm=ec_afgd5b --list=%s --out=%s"
        % (G, lst, out))
print((r.stdout or "").strip().splitlines()[-1], (r.stderr or "").strip()[:200])

one = os.path.join(G, "fix2", "dump", "list1_asset.txt")
r = run("python -W ignore -X utf8 %s\\center\\h62.py run --arm=ec_afgd5b --list=%s --out=%s"
        % (G, one, os.path.join(G, "fix2", "dump", "p1_asset_d5b.jsonl")))
print((r.stdout or "").strip(), (r.stderr or "").strip()[:200])
