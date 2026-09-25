# -*- coding: utf-8 -*-
"""Round 68 diag2 minimal synthetic witness for the else-branch linearisation defect.

Shape (mirrors IQEngine plugin_system_matcher/matcher.py::DefaultMatcher.match):
  * a `for` body whose first statement is an if/else (S0);
  * S0's THEN arm ends with two `if ...: continue` (S1, S2) so that S1's own region has
    no interior merge -- every path out of S1 goes to the loop header (back edge);
  * S0's ELSE arm also ends in a `continue`, so S0's merge point M is JOINED by a block
    that is NOT reachable from S1 (the else arm) as well as by S2's fall-through;
  * a statement S3 sits after M at the `for`-body level.
Because the analyzer computes region block-sets as "blocks reachable from the entry", M
(and everything after it, incl. S3) is pulled into S1.blocks while the else arm is not.
The generator's else-sequence walker then emits S3 *inside* S1's else arm, i.e. AFTER
the whole enclosing if/else, instead of leaving it to the parent sequence.
"""


def join_after_else(items, lim):
    for order in items:
        if order.kind:
            if order.a > lim:
                continue
            if order.b > lim:
                continue
        else:
            if order.c > lim:
                continue
            order.d = order.a
        if order.e:
            order.f = 1
        else:
            order.g = 2
        order.h = order.f
