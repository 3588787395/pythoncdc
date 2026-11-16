# g2c REAL46-004 min: %-format -> f-string whose {...} field holds a newline.
name = 'X'
failed_member = ['a', 'b']
failed = []
failed.append('%r member mismatch:\n      %s' % (
    name, '\n      '.join(failed_member),
))
print(failed)
