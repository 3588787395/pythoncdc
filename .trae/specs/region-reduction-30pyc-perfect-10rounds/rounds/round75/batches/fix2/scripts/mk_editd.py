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

anchor = """            has_user_code = any(
                instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                 'STORE_ATTR', 'STORE_SUBSCR',
                                 'BINARY_OP', 'UNARY_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                                 'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET',
                                 'IMPORT_NAME', 'IMPORT_FROM', 'LOAD_BUILD_CLASS',
                                 'GET_ITER', 'GET_AITER', 'FOR_ITER', 'YIELD_VALUE',
                                 'CALL', 'PRECALL', 'CALL_FUNCTION', 'CALL_METHOD')
                for instr in block.instructions
                if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP',
                                        'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                        'POP_EXCEPT', 'COPY', 'RERAISE', 'SWAP')
            )
            if has_user_code:
                continue
"""
assert u.count(anchor) == 1, u.count(anchor)

repl = """            has_user_code = any(
                instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                 'STORE_ATTR', 'STORE_SUBSCR',
                                 'BINARY_OP', 'UNARY_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                                 'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET',
                                 'IMPORT_NAME', 'IMPORT_FROM', 'LOAD_BUILD_CLASS',
                                 'GET_ITER', 'GET_AITER', 'FOR_ITER', 'YIELD_VALUE',
                                 'CALL', 'PRECALL', 'CALL_FUNCTION', 'CALL_METHOD')
                for instr in block.instructions
                if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP',
                                        'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                        'POP_EXCEPT', 'COPY', 'RERAISE', 'SWAP')
            )
            if has_user_code:
                # [R75 fix2 · edit-D] 清理扫描连续性（本方法上方 R07/「if-drop
                # Defect 3」注释已声明「WITH 清理区是连续的，终止于 WITH 自然出口」）：
                # 一旦扫过一块含用户代码（STORE/CALL/算术…）的块，其后的候选就不再
                # 与 with 出口连续——按地址序跨过真实语句继续吃块会把外层 if 之后的
                # 函数尾（纯 LOAD_CONST None; RETURN_VALUE）一并收进 WithRegion，
                # 该尾块随后被 with 发射在 if 体内（位置错位）。
                # 靶 IQCommon/util/trade_info_utils.pyc :: query_strategy_id（with
                # 位于 if-then 内，函数尾 @648 在外层 if/else 之后）与
                # query_trade_strategy_info（尾 @618）：扫描先跳过 `trade_df = df[...]`
                # 等用户语句，再吃到 @644/@648。改为到此为止：清理只收集与 with 出口
                # 连续的前缀，后续块交回顶层按地址序发射。
                # 判据只读「块内是否含用户代码指令类别」这一结构事实，不看函数名/
                # 文件名/偏移阈值/名字白名单；命中 continue 一侧的行为逐字不变。
                break
"""

spec = {"file": "core/cfg/region_analyzer.py",
        "edits": [{"anchor": anchor, "repl": repl}]}
out = os.path.join(D, "editd.json")
json.dump(spec, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out)

# merge with pad8_1f (same file)
pad = json.load(io.open(os.path.join(D, "pad8_1f.json"), encoding="utf-8"))
merged = {"file": "core/cfg/region_analyzer.py",
          "edits": list(spec["edits"]) + list(pad["edits"])}
mpath = os.path.join(D, "ad.json")
json.dump(merged, io.open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", mpath, "edits", len(merged["edits"]))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd %s %s"
        % (G, os.path.join(D, "ec_g.json"), mpath))
print(r.stdout, r.stderr)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s\\fix2\\dump\\ecafgd.txt %s\\fix2\\dump\\ecafgd_tiu.py" % (G, G, G))
print(r.stdout)
r = run("python -W ignore -X utf8 F:\\Downloads\\pythoncdc-main\\scripts\\pyc_verify.py single "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "--source %s\\fix2\\dump\\ecafgd_tiu.py" % G)
print(r.stdout)
