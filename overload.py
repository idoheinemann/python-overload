import inspect

__overloaded_functions = {}


def __func_name(func):
    name = f'{func.__module__}.{func.__qualname__}'
    return name


def __get_best_match(lst, name, *args, **kwargs):
    nominated = []
    for func in lst:
        specs = inspect.getfullargspec(func)
        func_args = specs.args
        kw_name = specs.varkw
        args_list = specs.varargs
        defaults = specs.defaults
        defaults = 0 if defaults is None else len(defaults)
        to_continue = False
        if len(func_args) - defaults > len(args) + len(kwargs):  # not enough arguments
            continue
        if kw_name is None:  # check for non existing argument
            for i in kwargs:
                if i not in func_args and i not in specs.kwonlyargs:
                    to_continue = True
                    break
            if to_continue:
                continue
        if args_list is None:
            if len(args) > len(func_args):  # too many arguments
                continue
        if args_list is None or len(args) <= len(func_args):
            filled_args = func_args[len(args):]
            for idx, i in enumerate(filled_args):  # unfilled argument
                if idx >= len(filled_args) - defaults:  # arguments with default value can be unfilled
                    break
                if i not in kwargs:  # argument not filled
                    to_continue = True
                    break
        else:
            filled_args = []
        if to_continue:
            break
        if kw_name is None and args_list is None:
            default_vars = func_args[len(func_args) - defaults:]
            filled_twice = 0
            for i in kwargs:
                if i in default_vars:
                    filled_twice += 1
            if len(args) > len(func_args) - defaults:
                filled_twice += len(args) - len(func_args) + defaults
            if len(func_args) != len(args) + len(kwargs) - filled_twice:  # amount of arguments not ok
                continue

        nominated.append(func)
    if len(nominated) == 0:
        raise AttributeError(f"no implementation of '{name}' matches given arguments")
    if len(nominated) > 1:
        raise AttributeError(f"too many possible implementations of {name} match the given arguments")
    return nominated[0]


def overload(func):
    name = __func_name(func)
    __overloaded_functions.setdefault(name, [])
    __overloaded_functions[name].append(func)

    return lambda *args, **kwargs: __get_best_match(__overloaded_functions[name], name, *args, **kwargs)(*args,
                                                                                                         **kwargs)


if __name__ == '__main__':
    @overload
    def x(a, b):
        return a + b


    @overload
    def x(a, b, c):
        return a + b + c


    @overload
    def y(*args, action=lambda a, b: a + b, start=0):
        import functools
        return functools.reduce(action, args, start)


    @overload
    def y(**kwargs):
        return kwargs


    class A:
        @overload
        def m(self, b, c, *args):
            return b, c, args

        @overload
        def m(self, b, **kwargs):
            return b, kwargs


    class B:
        @overload
        def __init__(self, x, y):
            self.x = x
            self.y = y

        @overload
        def __init__(self, x):
            self.__init__(x, 0)


    b1 = B(1)
    b2 = B(5, 6)

    print(y(5, 7, 8, action=lambda x, y: x * y, start=1))
    print(y(a=5, b=7))
    print(x(1, 2))
    print(x(1, 2, 3))
    a = A()
    print(a.m(1, 2, 3, 4))
    print(a.m(1))
    # print(a.m(10, c=5))
