import dis
dis.dis(compile('1 if a else 2 if b else 3', '<test>', 'exec'))
