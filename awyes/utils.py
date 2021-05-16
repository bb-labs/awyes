from functools import reduce


def sanitize_key(key):
    return int(key) if key.isnumeric() else key


def access(context, accessor):
    keys = accessor if isinstance(accessor, list) \
        else filter(None, accessor.split('.'))

    return reduce(
        lambda result, key: result[sanitize_key(key)],
        keys,
        context
    )


def insert(context, accessor, value):
    *target, final = accessor.split('.')

    access(context, target)[sanitize_key(final)] = value
