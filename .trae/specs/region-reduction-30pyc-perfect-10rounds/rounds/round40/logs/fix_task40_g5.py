# -*- coding: utf-8 -*-
"""Round 40 tasks.md correction, byte-level, inside the block this round appended (uncommitted).

The G5 subtask line quoted Round 39's canary sha and claimed 'before == after'.
Re-measured: it is false for Round 40. Replace that one line with the measured reading.
Preserves CRLF line endings, asserts everything before 'Task 40' is byte-identical.
"""
import hashlib
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/tasks.md'

OLD = ('          `site-packages/fly/data/quotationOK.py` sha `3f2242e73d7fd56a0096` 改前＝改后。\r\n')
NEW = ('          `site-packages/fly/data/quotationOK.py` 复测更正：`3f2242e73d7fd56a0096` 是 Round 39 的结转值'
       '（＝当时 HEAD blob 的 CRLF 形），本轮改后为 `b94d3247f7e4b49f48bb`（183 261 → 183 298 B，4 增 3 删）：'
       '`get_option_info` 内 `if/continue` 平铺被改渲为 `elif`/`else`，两支指令等价 ⇒ 官方 `143/143` 不变、'
       '严格尺 `change_his_to_forward`／`get_trend` 在双臂同为 still-defective。9 支承重金丝雀复测：'
       '3 支产物文本移动（另两支是 `plugin_manager` 孪生，`10/10`、`9/9` 均保持），0 支掉官方函数；'
       '全语料产物移动 36 支中 33 支官方计数不变、3 支上升、0 支下降（`logs/g5_canary_audit.txt`）。'
       '⇒ G5 金丝雀判据由「逐字节不变」更正为「承重文件不得掉官方函数」，'
       '下一轮基线重新导出到 `D:/Temp/r40gate/canary_shas_landed40.txt`。\r\n')

b = io.open(P, 'rb').read()
pre_sha = hashlib.sha256(b).hexdigest()[:20]
pre_len = len(b)
pre_crlf = b.count(b'\r\n')
i = b.find('Task 40'.encode('utf-8'))
assert i > 0
prefix_before = hashlib.sha256(b[:i]).hexdigest()[:20]
assert b.count(OLD.encode('utf-8')) == 1, 'G5 line not unique: %d' % b.count(OLD.encode('utf-8'))

out = b.replace(OLD.encode('utf-8'), NEW.encode('utf-8'), 1)
assert hashlib.sha256(out[:i]).hexdigest()[:20] == prefix_before, 'everything before Task 40 moved'
assert out.count(b'\r\n') == pre_crlf + 0, 'CRLF count changed (%d -> %d)' % (pre_crlf, out.count(b'\r\n'))
assert out.count(b'\n') == out.count(b'\r\n'), 'LF-only lines appeared'
assert out.count(b'3f2242e73d7fd56a0096') == b.count(b'3f2242e73d7fd56a0096'), \
    'the quoted sha must appear exactly where it did before (Round 38/39 entries stay)'
io.open(P, 'wb').write(out)
print('tasks.md: G5 line corrected in place; %d -> %d bytes, CRLF %d -> %d, sha20 %s -> %s'
      % (pre_len, len(out), pre_crlf, out.count(b'\r\n'), pre_sha,
         hashlib.sha256(out).hexdigest()[:20]))
