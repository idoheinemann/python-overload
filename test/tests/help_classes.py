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
    def x(self, a: int):
        return a + 3

    @overload
    def x(self, a, b, c):
        return a + b + c


class ThirdClass(SecondClass):
    @override
    def x(self, a: int):
        return a + 4

    @overload
    def x(self, a: float):
        return a * 2

    @override
    def x(self, a, b, c):
        return a + b + c + 2


class HelpClass:
    def a(self, x):
        return x
