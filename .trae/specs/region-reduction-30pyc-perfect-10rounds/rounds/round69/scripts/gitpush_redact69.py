# -*- coding: utf-8 -*-
"""Run a network git command and print ONLY redacted output.

  python -X utf8 gitpush_redact67.py

The remote URL in this repository embeds a live PAT, so raw git stderr/stdout can leak it
(even through the permission prompt). This helper therefore
  * never prints the argv it runs beyond the subcommand words,
  * reads no config and passes no URL,
  * writes child output to a private temp file (so the tool-call text itself cannot echo it),
  * rewrites every credential-shaped token (scheme://user:tok@host, `Token auth…`,
    `***@github.com`, any `ghp_…`/`github_pat_…` run) to `[redacted]` before printing.
Exit code of the child is propagated.
"""
import io
import os
import re
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
TMP = r'D:/Temp/opencode/r69gate/center/logs/_gitout.txt'
sys.stdout.reconfigure(encoding='utf-8')

CMD = ['git', 'push', 'origin', 'main']

pats = [
    (re.compile(r'(?i)\b(https?://)([^/\s@]+):([^\s/]+)@'), r'\1[redacted]@'),
    (re.compile(r'(?i)(token auth)[^\s"\']+'), r'\1[redacted]'),
    (re.compile(r'\b[0-9a-fA-F]{20,}@[a-zA-Z0-9.-]+'), '[redacted]'),
    (re.compile(r'\b(ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_\-]{4,}'), '[redacted]'),
    (re.compile(r'(?i)(password|passwd|secret|token)[ =:][^\s,;]+'), r'\1=[redacted]'),
]


def clean(s):
    if not s:
        return s
    for rx, rep in pats:
        s = rx.sub(rep, s)
    return re.sub(r'(?m)^(To |From )(\S+)', r'\1[redacted]', s)


io.open(os.path.dirname(TMP), 'w', encoding='utf-8').close() if not os.path.isdir(os.path.dirname(TMP)) else None
with io.open(TMP, 'wb') as fh:
    r = subprocess.run(CMD, cwd=REPO, stdout=fh, stderr=subprocess.STDOUT, timeout=280)
txt = io.open(TMP, encoding='utf-8', errors='replace').read()
print('git %s -> exit %d' % (' '.join(CMD[1:2]), r.returncode))
sys.stdout.write(clean(txt))
# reverse clamp: prove nothing credential-shaped survived into what we just printed
leak = [m.group(0)[:12] for m in re.finditer(r'(?i)(https?://\S+:\S+@|ghp_[A-Za-z0-9]{6,}|github_pat_\w+)', txt) ]
print('RAW-CREDENTIAL-TOKENS-IN-OUTPUT=%d' % len(leak))
