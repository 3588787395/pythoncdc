# fix161b.py: rr-v5r161 [v161-NOTMIX] 外科收窄——走查尾重分类守卫
# len(chain) >= 2 → len(chain) >= 3（只改这一处 + 注释同步；fix161.py 历史存档不动）。
#
# 根因（矩阵实证 matrix_v5r161_result.txt C161_not_or HEAD-TEXT-DIFF）：
#     双成员链 [A,B]（`if not a or b:` 纯 or 链，无 and 子链）也命中走查尾
#     重分类，链首被改 'or' 后走 or→and 边界装配，产物多出 `else:` 分支
#     （判官仍 EQUAL，纯风格漂移）。按「零触碰」纪律控制案必须 SAME。
#     本族目标是 or→and 混合链：and 子链 ≥2 成员，即整链 ≥3。
#
# 收窄：守卫改 len(chain) >= 3；W14/R3-K/R53 三门保持原样——双成员链仍会
#     登记 _v161_or_head_exit 并续接，但走查尾不重分类，装配路径与 HEAD
#     逐字节一致（narrow_check.py 9 案判官 + 文本对照实证）。
import io

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
MARKER = 'v161-NOTMIX'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s
N = 0


def rep(old, new, expect=1):
    global s, N
    c = s.count(old)
    assert c == expect, 'anchor count %d (expect %d): %r' % (c, expect, old[:80])
    s = s.replace(old, new, expect)
    N += 1


# [1] 「精确形 =」描述同步：整链 ≥3（and 子链 ≥2 成员）前置条件
rep("        # 精确形 = 链首 'and' 且 FALSE 极性 ∧ 链首跳转目标 = 末成员",
    "        # 精确形 = 整链 ≥3（and 子链 ≥2 成员）∧ 链首 'and' 且 FALSE 极性 ∧ 链首跳转目标 = 末成员")

# [2] 注释块末尾追加两行 + 守卫收窄 >= 2 → >= 3（唯一匹配）
rep("""        # 既有尾部判定（C3）。
        if (len(chain) >= 2
                and chain[0][1] == 'and'
                and _v161_or_head_exit is not None):""",
"""        # 既有尾部判定（C3）。
        # 子链 ≥2 成员（整链 ≥3）才是 or→and 混合形：双成员纯 or 链
        # （`not a or b`）维持既有装配路径，零触碰（C161_not_or 实证）。
        if (len(chain) >= 3
                and chain[0][1] == 'and'
                and _v161_or_head_exit is not None):""")

assert s != orig
assert s.count(MARKER) == 5, 'marker count %d' % s.count(MARKER)
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix161b applied: %d replacements, %d markers' % (N, s.count(MARKER)))

import py_compile
py_compile.compile(PATH, doraise=True)
print('syntax OK')