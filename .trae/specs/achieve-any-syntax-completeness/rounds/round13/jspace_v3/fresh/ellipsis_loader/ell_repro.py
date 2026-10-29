# Minimal repro: Ellipsis const rendered as None inside call args.
X = type(...)
Y = {type(...): 'Ellipsis'}
Z = (type(...),)
print('X', X, 'Y', Y, 'Z', Z)
