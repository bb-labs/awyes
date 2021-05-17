from functools import reduce


def sanitize_key(key):
    return int(key) if key.isnumeric() else key


def subscript(context, key):
    try:
        return context[sanitize_key(key)]
    except:
        return getattr(context, sanitize_key(key))


def access(context, accessor):
    a = accessor
    keys = a if isinstance(a, list) else filter(None, a.split('.'))

    return reduce(
        lambda result, key: subscript(result, key),
        keys,
        context
    )


def insert(context, accessor, value):
    *target, final = accessor.split('.')

    access(context, target)[sanitize_key(final)] = value
