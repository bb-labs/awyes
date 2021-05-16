from itertools import chain
from functools import reduce


def sanitize_key(key):
    return int(key) if key.isnumeric() else key


def access(value, accessor):
    keys = filter(None, chain.from_iterable(map(
        lambda dotstring: dotstring.split('.'),
        accessor.split(':')
    )))

    return reduce(lambda result, key: result[sanitize_key(key)], keys, value)


def topological_sort(deployment):
    pass
