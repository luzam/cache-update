import pylibmc
from pylibmc import Client
import six
import time
import logging

pylibmc_version = "old" if pylibmc.__version__ == "1.5.2" else "new"

# wait for memcached
time.sleep(1)

my_prefix = "py2" if six.PY2 else "py3"
my_prefix += "-" + pylibmc_version
prefixes = ["py2-old", "py2-new", "py3-new"]
# prefixes.remove(my_prefix)


if pylibmc_version == "old":
    c = Client(
        ["cache:11211"],
    )
else:
    c = Client(["cache:11211"], behaviors={"pickle_protocol": 2})


class Toto(object):
    g = 3

    def __init__(self):
        self.s = 4

    def __eq__(self, other):
        return self.g == other.g and self.s == other.s

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "[{}][{}]".format(self.g, self.s)


class OldStyleToto:
    g = 3

    def __init__(self):
        self.s = 4

    def __eq__(self, other):
        return self.g == other.g and self.s == other.s

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return "[{}][{}]".format(self.g, self.s)


c.set(my_prefix + "bool", True)
c.set(my_prefix + "int", 42)
c.set(my_prefix.encode() + b"int", 42)
c.set(my_prefix + "float", 0.3145)
c.set(my_prefix + "list", [1, None, True])
c.set(my_prefix + "dict", {"1": 32, 33: True})
c.set(my_prefix + "set", {3, 5, 7, False})

c.set(my_prefix + "uni", u"uni")
c.set(my_prefix + "binstr", b"binstr")
c.set(my_prefix + "toto", Toto())
c.set(my_prefix + "oldClassStyle", OldStyleToto())
c.set(my_prefix + "dictStr", {"key":42})


# wait for everybody
time.sleep(0.5)


def check(prefix, key, expect):
    fkey = prefix + key
    try:
        value = c.get(fkey)
        if expect != value:
            print(
                "EE:NOT THE SAME VALUE {} -> {} for {} expecting [{}{}] got [{}{}]".format(
                    prefix, my_prefix, key, type(expect), expect, type(value), value
                )
            )
    except Exception as e:
        logging.error(
            "EE:GET FAILED  {} -> {} for {} expecting [{}{}]".format(
                prefix, my_prefix, key, type(expect), expect
            )
        )


for p in prefixes:
    # root boolean is special, we removed them because pylibmc 1.5.2 -> 1.6.1 transform them in string
    # The ok ones
    check(p, "int", 42)
    check(p.encode(), b"int", 42)
    check(p, "float", 0.3145)
    check(p, "list", [1, None, True])
    check(p, "dict", {"1": 32, 33: True})
    check(p, "set", {3, 5, 7, False})
    check(p, "binstr", b"binstr")
    check(p, "toto", Toto())

    # The not ok ones :

    # set unicode in 1.6.1 -> get in 1.5.2: not compatible for <unicode>: 1.5.2 is pickled, 1.6.1 is unicode FLAG
    # set unicode 1.5.2 -> get in 1.6.1 is working
    # https://sendapatch.se/projects/pylibmc/changelog.html#new-in-version-1-6-0
    check(p, "uni", u"uni")

    # Boolean
    # https://sendapatch.se/projects/pylibmc/changelog.html#new-in-version-1-6-0
    # but we dont have those anymore in the codebase
    check(p, "bool", 1)

    # Old class style (class no inheriting from object explicitely)
    # but we dont have those anymore in the codebase
    check(p, "oldClassStyle", OldStyleToto())

    # the classic bytes vs string
    check(p, "str", "str")
    