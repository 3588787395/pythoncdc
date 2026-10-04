# Source Generated with Decompyle++ (Python version)
# File: r10_03_import_nested_hosts.pyc (Python 3.11)

__doc__ = 'r10_03: import 深层嵌套宿主（def>for>if>import / while>try>import / class>def>if>import，深度 ≥3）'
class Host:
    def method(self, n):
        if n > 0:
            from deep.nest import thing
            return thing(n)
        else:
            return None
def imp_in_def_for_if(rows):
    total = 0
    for r in rows:
        if r > 0:
            from deep.host import helper
            total += helper(r)
    return total
def imp_in_while_try(limit):
    out = []
    i = 0
    while i < limit:
        try:
            from deep.host import loader
            out.append(loader(i))
        except ValueError:
            break
        i += 1
    return out
