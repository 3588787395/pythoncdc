# -*- coding: utf-8 -*-
"""Build the R21-26 narrowed candidate on the gate-32 sealed base.

Pieces ported from r50a's build 78f88001394ed59b (gate-31 base):
  1. _r45a_else_is_implicit_tail_only helper (r50 lines 371-400)
  2. R44A-elif dispatch block (r50 lines 2399-2466) minus _r50pre/_r50fire
     probe calls, plus the measured a2 narrowing (len(body) > 1)
  3. guard call-site 2-line change (r50 lines 8636-8637)
Probe scaffolding (_r50_* logging) is deliberately NOT ported.
"""
import hashlib
import io
import sys

BASE = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_ast_generator.py'
R50 = 'D:/Temp/r30chkC/core/cfg/region_ast_generator.py'
OUT = 'D:/Temp/r33/CANDIDATE_region_ast_generator.py'

base_b = open(BASE, 'rb').read()
r50_b = open(R50, 'rb').read()

def split(b):
    lines = b.split(b'\n')
    out = []
    for i, l in enumerate(lines):
        if i < len(lines) - 1:
            out.append(l + b'\n')
        else:
            out.append(l)  # last, possibly empty
    return out

base = split(base_b)
r50 = split(r50_b)

assert base_b.startswith(b'\xef\xbb\xbf'), 'base lost BOM'
assert base[0].endswith(b'\r\n'), 'base is not CRLF'
assert r50_b.startswith(b'\xef\xbb\xbf'), 'r50 lost BOM'

def L(lines, n):
    """1-based line bytes without ending."""
    return lines[n - 1].rstrip(b'\r\n')

# ---- anchor asserts on base ----
assert L(base, 368) == b'    return False', L(base, 368)
assert L(base, 371).startswith(b'class RegionASTGenerator:'), L(base, 371)
assert L(base, 2023) == L(r50, 2397), (L(base, 2023), L(r50, 2397))
assert L(base, 2024) == b'                if isinstance(region_ast, list):', L(base, 2024)
assert L(base, 8275) == b'                    and _r2114_else_owned_skipped == len(_filtered_else_blocks)):', L(base, 8275)
assert L(base, 8273) == b'            if (not else_stmts', L(base, 8273)

# ---- sanity asserts on r50 source pieces ----
assert L(r50, 371).startswith(b'def _r45a_else_is_implicit_tail_only(gen, blocks):'), L(r50, 371)
assert L(r50, 400) == b'    return True', L(r50, 400)
assert L(r50, 2398).startswith(b'                _r50pre(self,'), L(r50, 2398)
assert L(r50, 2399).startswith(b'                # [R44A-elif]'), L(r50, 2399)
assert L(r50, 2413) == b"                                 region_ast['body'][-1]))", L(r50, 2413)
assert L(r50, 2428).startswith(b'                    _r50fire(self,'), L(r50, 2428)
assert L(r50, 2429).startswith(b'                    _r44a_mb = region.merge_block'), L(r50, 2429)
assert L(r50, 2466).startswith(b'                                self.generated_offsets.add('), L(r50, 2466)
assert L(r50, 8636) == b'                    and _r2114_else_owned_skipped == len(_filtered_else_blocks)', L(r50, 8636)
assert L(r50, 8637) == b'                    and not _r45a_else_is_implicit_tail_only(self, _filtered_else_blocks)):', L(r50, 8637)

# ---- piece 1: helper (r50 371-400) + two trailing blanks ----
helper = r50[370:400]  # idx 370..399 = lines 371..400
assert helper[0].startswith(b'def _r45a_else_is_implicit_tail_only')
helper_block = helper + [b'\r\n', b'\r\n']

# ---- piece 2: dispatch, probe-free + a2 ----
pred = r50[2398:2427]   # idx 2398..2426 = lines 2399..2427
body = r50[2428:2466]   # idx 2428..2465 = lines 2429..2466
assert pred[0].startswith(b'                # [R44A-elif]')
assert body[0].startswith(b'                    _r44a_mb = region.merge_block')

a2_comment = (
    b'                        # [R21-26-a2] '
    + '只当 then 臂在尾随 return None 之前还有真实语句时才收编：臂仅剩一条'
      'return None 时（canary: check_is_valid_date / show_func），剥掉尾随'
      'return None 等于删掉整条臂，折叠后函数的隐式 return None 尾被'
      'JUMP_FORWARD 顶掉（delta=-1）。全语料 fire census 13 处中 a2=T 仅'
      'handlers._target 一处，六处误伤全部 a2=F。'.encode('utf-8')
    + b'\r\n'
)
a2_line = b'                        and len(region_ast.get(\'body\') or []) > 1\r\n'
# insert after line 2413 (idx 2412) which is pred[14]
assert L(r50, 2413) == pred[14].rstrip(b'\r\n')
dispatch = pred[:15] + [a2_comment, a2_line] + pred[15:] + body

# ---- assemble ----
out = []
out.extend(base[:370])            # lines 1..370 (idx 0..369)
out.extend(helper_block)          # helper + 2 blanks
out.extend(base[370:2023])        # lines 371..2023 (idx 370..2022)
out.extend(dispatch)              # dispatch block
out.extend(base[2023:8274])       # lines 2024..8274 (idx 2023..8273)
out.extend([r50[8635], r50[8636]])  # the two-line guard replacement
out.extend(base[8275:])           # lines 8276.. (idx 8275..)

data = b''.join(out)
open(OUT, 'wb').write(data)

# ---- verification ----
import ast as _ast
text = data.decode('utf-8-sig')
_ast.parse(text)
compile(text, OUT, 'exec')
print('OK wrote', OUT)
print('bytes', len(data), 'sha16', hashlib.sha256(data).hexdigest()[:16])
print('base bytes', len(base_b), 'delta', len(data) - len(base_b))
nl = data.count(b'\n')
crlf = data.count(b'\r\n')
print('LF', nl, 'CRLF', crlf, 'bare LF', nl - crlf)
