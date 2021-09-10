import unittest
from test.tests.help_classes import HelpClass, FirstClass, SecondClass, ThirdClass


class TestOverride(unittest.TestCase):
    def test_get_defining_class(self):
        from overload.overload import get_defining_class
        a = get_defining_class(HelpClass.a)
        self.assertEqual(a, HelpClass)

    def test_override(self):
        t = ThirdClass()
        self.assertEqual(t.x(1), 5)
        self.assertEqual(t.x(1.1), 2.2)
        self.assertEqual(t.x(1, 2, 3), 8)
        x = SecondClass()
        self.assertEqual(x.x(1), 4)
        a = FirstClass()
        self.assertEqual(a.x(1), 1)
        self.assertEqual(x.x(1, 2), 3)
        self.assertEqual(x.x(1, 2, 3), 6)
