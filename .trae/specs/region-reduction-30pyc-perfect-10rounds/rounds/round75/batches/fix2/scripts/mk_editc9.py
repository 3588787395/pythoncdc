import io, os, sys, subprocess, json
sys.stdout.reconfigure(encoding="utf-8")

REPO = r"F:\Downloads\pythoncdc-main"
OUT = r"D:\Temp\opencode\r75gate\fix2\specs"
os.makedirs(OUT, exist_ok=True)

path = os.path.join(REPO, "core", "cfg", "region_ast_generator.py")
src = io.open(path, encoding="utf-8-sig", newline="").read()
nl = "\r\n" if "\r\n" in src else "\n"
u = src.replace(nl, "\n")

anchor = ("        if region.region_type.name == 'IF_ELIF_CHAIN':\n"
          "            return self._if_generate_full_elif_chain(region)\n")
assert u.count(anchor) == 1, u.count(anchor)

guard = """        # [R75 fix2 · edit-C] 区域归约算法原则 2（每块唯一归属）：祖先 IfRegion 的
        # merge_block 是祖先 if/else 两路汇合点，位置必然在祖先 if 之后；任何嵌套在
        # 祖先 then 臂内的子 IfRegion 都不得把它收进自己的 else 臂，否则祖先的汇合
        # 语句会被发射进祖先 if 的 then 体内（越界吸收）。区域构建自内向外（内层先建），
        # 祖先 merge 此时不可知，故本判据放在生成侧：祖先 _generate_if 先于子区域执行。
        # 靶 IQCommon/util/trade_info_utils.pyc :: trade_operation：IfRegion(entry=656,
        # merge=1000, 无 else) 的 then 内嵌 IfRegion(entry=726, else=[874,886,896,908,
        # 918,1000]) 吸收了 1000，`write_info.append(items)` 被压进
        # `if items[0] in trade_id_list:` 体内，重编译后条件假分支由 1000 改跳 1042
        # （跳过 append），CFG 不等价。摘出后 1000 归还父层按地址序发射，落在祖先 if
        # 之外的 for 体内。判据只读结构事实：(a) 祖先为无 else 的 IfRegion、(b) 子区域
        # entry 介于祖先 entry 与 merge 之间且在祖先 then 臂内、(c) 子区域是 IfRegion、
        # (d) 其 else 臂含祖先 merge、(e) 满足者恰为 1 个（多主张者不裁决，避免误摘）。
        # 不读偏移常量/名字/历史清单；不命中时逐字节不变。
        _r75c_m = getattr(region, 'merge_block', None)
        _r75c_e0 = getattr(getattr(region, 'entry', None), 'start_offset', None)
        _r75c_mm = getattr(_r75c_m, 'start_offset', None)
        _r75c_rtype = getattr(getattr(region, 'region_type', None), 'name', None)
        _r75c_then = getattr(region, 'then_blocks', None) or []
        _r75c_else = getattr(region, 'else_blocks', None) or []
        if (_r75c_m is not None and _r75c_e0 is not None and _r75c_mm is not None
                and _r75c_rtype in ('IF_THEN', 'IF')
                and _r75c_else == []):
            _r75c_claims = []
            for _r75c_r in list(getattr(self, 'regions', None) or []):
                if _r75c_r is region:
                    continue
                _r75c_reo = getattr(getattr(_r75c_r, 'entry', None),
                                    'start_offset', None)
                if _r75c_reo is None or not (_r75c_e0 < _r75c_reo < _r75c_mm):
                    continue
                if not any(b is _r75c_r.entry for b in _r75c_then):
                    continue
                _r75c_cname = getattr(getattr(_r75c_r, 'region_type', None),
                                      'name', None) or ''
                if not _r75c_cname.startswith('IF_'):
                    continue
                _r75c_lst = getattr(_r75c_r, 'else_blocks', None)
                if (_r75c_lst and len(_r75c_lst) >= 2
                        and _r75c_lst[-1] is _r75c_m
                        and all(b is not _r75c_m for b in _r75c_lst[:-1])):
                    _r75c_claims.append(_r75c_r)
            if len(_r75c_claims) == 1:
                _r75c_r = _r75c_claims[0]
                _r75c_r.else_blocks = [b for b in _r75c_r.else_blocks
                                       if b is not _r75c_m]
                _r75c_bl = getattr(_r75c_r, 'blocks', None)
                if _r75c_bl is not None:
                    try:
                        _r75c_bl.discard(_r75c_m)
                    except Exception:
                        pass
"""

spec = {"file": "core/cfg/region_ast_generator.py",
        "edits": [{"anchor": anchor, "repl": guard + anchor}]}
out = os.path.join(OUT, "editc9.json")
json.dump(spec, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out)


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


print(run("python -W ignore -X utf8 D:\\Temp\\opencode\\r75gate\\center\\h62.py build "
          "--spec=%s --dst=editc7" % out).stdout)

SP = r"F:\Downloads\pythoncdc-main\site-packages"
DUMP = r"D:\Temp\opencode\r75gate\fix2\dump"
for f in [r"IQEngine\plugins\plugin_system_matcher\matcher.pyc",
          r"IQEngine\plugins\plugin_system_trade\trade_live_broker.pyc",
          r"IQCommon\util\trade_info_utils.pyc"]:
    dst = os.path.join(DUMP, "e7_" + f.replace("\\", "_"))
    r = run("python -W ignore -X utf8 D:\\Temp\\opencode\\r75gate\\fix2\\run_dbg.py "
            "editc7 %s %s %s" % (os.path.join(SP, f), os.path.join(DUMP, "e7.txt"), dst))
    print(f, "->", [l for l in (r.stdout or "").splitlines() if "decompiled" in l])
    print("    verify:", end=" ")
    v = run("python -W ignore -X utf8 %s\\scripts\\pyc_verify.py single %s --source %s"
            % (REPO, os.path.join(SP, f), dst))
    print([l for l in (v.stdout or "").splitlines() if "[single] status" in l])
