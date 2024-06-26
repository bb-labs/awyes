import json
import textwrap
import functools


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_status(value, status=Colors.OKGREEN, indicator=""):
    print(
        textwrap.indent(
            (value if type(value) is str else json.dumps(value, indent=2, default=str)),
            f"{status}{indicator} {Colors.ENDC}",
            lambda _: True,
        )
    )


def sanitize_key(key):
    try:
        return int(key)
    except Exception:
        return key


def subscript(context, key):
    try:
        return context[sanitize_key(key)]
    except Exception:
        return getattr(context, sanitize_key(key))


def rgetattr(context, accessor):
    a = accessor
    keys = a if isinstance(a, list) else filter(None, a.split("."))

    return functools.reduce(lambda result, key: subscript(result, key), keys, context)


def rsetattr(context, accessor, value):
    *target, final = accessor.split(".")

    rgetattr(context, target)[sanitize_key(final)] = value
