from functools import reduce


def sanitize_key(key):
    return int(key) if key.isnumeric() else key


def subscript(context, key):
    try:
        return context[sanitize_key(key)]
    except Exception:
        return getattr(context, sanitize_key(key))


def rgetattr(context, accessor):
    a = accessor
    keys = a if isinstance(a, list) else filter(None, a.split('.'))

    return reduce(
        lambda result, key: subscript(result, key),
        keys,
        context
    )


def rsetattr(context, accessor, value):
    *target, final = accessor.split('.')

    rgetattr(context, target)[sanitize_key(final)] = value
