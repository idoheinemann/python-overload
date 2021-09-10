from overload import overload, override


class FirstClass:
    @overload
    def x(self, a):
        return a

    @overload
    def x(self, a, b):
        return a + b


class SecondClass(FirstClass):
    @override
    def x(self, a):
        return a + 3


class HelpClass:
    def a(self, x):
        return x
