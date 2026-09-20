# -*- coding: utf-8 -*-
"""R13-L 复现：`for ... else:` 区域未被识别 —— else 体被当成循环体尾部的
fall-through 内联，循环内的 `break`（POP_TOP + JUMP_FORWARD）退化成合成 POP_TOP，
`if` 的假边被重定向，for 回边与 else 块丢失一份。

对应真实目标：
  IQEngine/utils/logger/handlers.pyc
      <module>.RotatingFileHandler.perform_rollover  [seq_len] orig=127 decomp=125

实测 dis（ORIG，带 co_lines 行号归属；见 D:/Temp/r13/probe_break_else.py 证明
`for: ... if c: break / else: ...` 在 3.11 里正是这个形状）：
  ORIG   194 L132 POP_JUMP_FORWARD_IF_FALSE  ->200
         196 L133 POP_TOP                     <- `break` 弹掉 for 的迭代器
         198 L133 JUMP_FORWARD               ->306   （跳到 for/else 之后）
         200 L132 JUMP_BACKWARD              ->106   （循环回边）
         202 L135 .. else 体（rename/_open/return）
         306 L138 .. for/else 之后的第二个 for
  DECOMP 196 L89 POP_JUMP_FORWARD_IF_FALSE   ->516   （假边被重定向到 else 拷贝）
         198 L90 LOAD_GLOBAL 'xrange'                （else 体之后的代码被内联进 if 体）
         ...
         616 L102 POP_TOP                             （合成 break，只此一条，无 JUMP_BACKWARD）
         622 L103 rename/_open/return 的第二份拷贝
  净差 = ORIG 多 3 条（POP_TOP/JUMP_FORWARD/JUMP_BACKWARD）、DECOMP 多 1 条 POP_TOP
        => 127 vs 125，与 ruler 报告一致。
"""


class RotatingFileHandler(object):

    def __init__(self, filename, backup_count, rename, exists, system_log, errno_mod):
        self._filename = filename
        self.backup_count = backup_count
        self._rename = rename
        self._exists = exists
        self._log = system_log
        self._errno = errno_mod

    def _open(self, mode):
        return None

    def perform_rollover(self):
        x = 0
        src = None
        for x in range(self.backup_count - 1, 0, -1):
            src = '%s.%d' % (self._filename, x)
            if self._exists(src):
                break
        else:
            self._rename(self._filename, self._filename + '.1')
            self._open('w')
            return
        for i in range(x, 0, -1):
            src = '%s.%d' % (self._filename, i)
            dst = '%s.%d' % (self._filename, i + 1)
            try:
                self._rename(src, dst)
            except OSError:
                self._log.error('oops')
                if self._errno != 2:
                    raise
        self._rename(self._filename, self._filename + '.1')
        self._open('w')
        return
