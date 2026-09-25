# -*- coding: utf-8 -*-
def wret(path, kind):
    try:
        with open(path, 'w', encoding='utf-8') as fw:
            if kind == 'a':
                fw.write('a')
                return True
            elif kind == 'b':
                fw.write('b')
                return True
            else:
                fw.write('e')
            return False
    except BaseException:
        return False
