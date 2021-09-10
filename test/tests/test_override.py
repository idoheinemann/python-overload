import unittest
from test.tests.help_classes import HelpClass, FirstClass, SecondClass


class TestOverride(unittest.TestCase):
    def test_get_defining_class(self):
        from overload.overload import get_defining_class
        a = get_defining_class(HelpClass.a)
        self.assertEquals(a, HelpClass)
        def f(x):
            pass
        b = get_defining_class(f)

    def test_override(self):
        x = SecondClass()
        self.assertEquals(x.x(1), 4)
