import unittest
from test.tests.help_classes import HelpClass, FirstClass, SecondClass, ThirdClass


class TestOverride(unittest.TestCase):
    def test_get_defining_class(self):
        from overload.overload import get_defining_class
        a = get_defining_class(HelpClass.a)
        self.failUnlessEqual(a, HelpClass)

    def test_override(self):
        t = ThirdClass()
        self.failUnlessEqual(t.x(1), 5)
        self.failUnlessEqual(t.x(1, 2, 3), 8)
        x = SecondClass()
        self.failUnlessEqual(x.x(1), 4)
        a = FirstClass()
        self.failUnlessEqual(a.x(1), 1)
        self.failUnlessEqual(x.x(1, 2), 3)
        self.failUnlessEqual(x.x(1, 2, 3), 6)
