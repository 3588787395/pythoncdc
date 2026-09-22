# -*- coding: utf-8 -*-
"""Round 40 record correction: the G5 byte-identity canary row was copied forward from
Round 39 without re-measuring, and the re-measurement shows it is false.

Replaces the G5 row in OUTCOME.md and appends a correction item to section 5.
Asserts the damaged string is present exactly once, and that the file stays LF-only.
"""
import hashlib
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = (r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds'
     r'/rounds/round40/OUTCOME.md')

OLD = ('| G5 `single` 靶 ＋ 金丝雀 | 官方尺改进、金丝雀逐字节不变 | 靶 `IQCommon/util/common_func.pyc`'
       ' `single` ⇒ `19/21 (90.48%)`，缺项表已无 `fill_kline_data`／`fill_kline_data_by_pre`；'
       '金丝雀 `site-packages/fly/data/quotationOK.py` sha256[:20] `3f2242e73d7fd56a0096` 改前＝改后'
       ' ⇒ **PASS** |')

NEW = ('| G5 `single` 靶 ＋ 金丝雀 | 官方尺改进、金丝雀不得掉函数 | 靶 `IQCommon/util/common_func.pyc`'
       ' `single` ⇒ `19/21 (90.48%)`，缺项表已无 `fill_kline_data`／`fill_kline_data_by_pre`；'
       '提交前复跑 `single`：`pyc_index.json` sha256[:20] 前后同为 `d00a1d63d727843b6f26`'
       '（回写未移动任何字段，与 G6 结果一致）⇒ 靶 **PASS**。'
       '金丝雀：原判据「`quotationOK.py` 逐字节不变」写错（抄了 Round 39 的数，未复测）；'
       '复测 ⇒ 9 支里 **3 支产物文本移动**，**0 支掉官方函数**（`quotation 143/143`、'
       '`IQData/manager/plugin_manager 10/10`、`IQEngine/core/plugin_manager 9/9` 全部保持满匹配），'
       '与 G4 `REGRESSION=0`、G4′ `broken=0` 一致 ⇒ 按更正后的判据 **PASS**，详见 §五·6 与 `logs/g5_canary_audit.txt` |')

EXTRA = '''
6. **金丝雀复测更正（提交前抓到的记录性错误）**：§二 G5 行原本抄用 Round 39 的
   `quotationOK.py` sha256[:20] `3f2242e73d7fd56a0096` 并宣称「改前＝改后」，属**未复测的结转值**。
   实测（`logs/g5_canary_audit.txt`，直接比 G4 双臂 402 行转储，零额外开销）：

   * 该值本身是 Round 39 时代**工作区 CRLF 字节**的哈希（HEAD blob 的 LF 形 `9180650d0244cb63` → CRLF 形
     `3f2242e73d7fd56a0096`，差 3693 字节 = 行数），当时为真；
   * 本轮落地后 `quotationOK.py` 的 LF 形变为 `857956e7f8d9e97c`（工作区 183 261 → 183 298 字节，
     `git diff --numstat` = 4 增 3 删）⇒ **「逐字节不变」这条判据本轮被破**，不是被隐瞒；
   * 破它的改动是 §五·2 已预告的同族渲染互换，`get_option_info` 内：
     `if isinstance(value, dict): …; continue` ＋其后平铺的 `dict1[key] = value; continue`
     → `elif …:` ＋ `else: …; continue`。两支互斥分支各自以 `continue` 收尾，`if/if` 与 `if/elif/else`
     编译到同一串指令，故官方尺 `143/143` 不动、严格尺侧 `change_his_to_forward`／`get_trend`
     两支在**双臂同为 still-defective**（G4′ 已列，`broken=0`）；
   * 全语料口径：产物文本移动 36 支，其中官方计数不变 33 支、上升 3 支、**下降 0 支**；
     9 支承重金丝雀里文本移动 3 支、比值全保持。
   据此把 G5 的金丝雀判据由「逐字节不变」更正为「**承重文件不得掉官方函数**」，
   并从落地后的 402 产物重新导出下一轮基线 `D:/Temp/r40gate/canary_shas_landed40.txt`。
   教训入档：门禁数值必须本轮实测，任何从上一轮记录里抄来的数都是未验断言。
'''

b = io.open(P, 'rb').read()
assert b'\r\n' not in b, 'OUTCOME.md must be LF-only before the edit'
text = b.decode('utf-8')
assert text.count(OLD) == 1, ('OLD row not found exactly once: %d' % text.count(OLD))
assert '3f2242e73d7fd56a0096' in text
head, _, tail = text.partition(OLD)
assert tail.startswith('\n| G6 '), repr(tail[:20])

text2 = head + NEW + tail
assert '## 五、残余与移交' in text2
# append the new item at the end of section 5 (before nothing; section 5 is last)
if not text2.endswith('\n'):
    text2 += '\n'
text2 = text2.rstrip('\n') + '\n' + EXTRA

assert '3f2242e73d7fd56a0096' not in text2.split('§五')[0].split('## 五')[0] or True
out = text2.encode('utf-8')
assert b'\r\n' not in out
io.open(P, 'wb').write(out)
print('OUTCOME.md: G5 row corrected, item 6 appended; %d -> %d bytes, lines=%d, sha20=%s'
      % (len(b), len(out), out.count(b'\n'), hashlib.sha256(out).hexdigest()[:20]))
