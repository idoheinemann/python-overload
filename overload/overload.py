import inspect
from functools import wraps, partial
import typing
from typing import _GenericAlias, _SpecialForm
import collections.abc as abc_col
import sys

__overloaded_functions = {}
__override_queue = set()


def __compare_specs(f1, f2):
    s1 = inspect.getfullargspec(f1)
    s2 = inspect.getfullargspec(f2)
    if len(s1.args) != len(s2.args):
        return False
    if type(s1.varargs) is not type(s2.varargs):
        return False
    if type(s1.varkw) is not type(s2.varkw):
        return False
    if set(s1.kwonlyargs) != set(s2.kwonlyargs):
        return False
    for i, v in enumerate(s1.args):
        ann1 = f1.__annotations__.get(v)
        if ann1 is None:
            continue
        ann2 = f2.__annotations__.get(s2.args[i])
        if ann2 is None:
            continue
        if ann1 != ann2:
            return False
    return True


def __get_meth_class_name(meth):
    name = meth.__qualname__.rsplit('.', 1)
    if '<locals>' in name[0] or len(name) == 1:
        return ''
    return name[0]


def __get_class_that_defined_method(meth):
    if isinstance(meth, partial):
        return __get_class_that_defined_method(meth.func)
    if inspect.ismethod(meth) or (
            inspect.isbuiltin(meth) and getattr(meth, '__self__', None) is not None and getattr(meth.__self__,
                                                                                                '__class__', None)):
        for cls in inspect.getmro(meth.__self__.__class__):
            if meth.__name__ in cls.__dict__:
                return cls
        meth = getattr(meth, '__func__', meth)  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth), __get_meth_class_name(meth), None)
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects


def get_defining_class(meth):
    return __get_class_that_defined_method(meth)


def __func_name(func):
    name = f'{func.__module__}.{func.__qualname__}'
    return name


__SINGLE_ATTR_DICT = {
    abc_col.Sized: '__len__',
    abc_col.Awaitable: '__await__',
    abc_col.Hashable: '__hash__',
    abc_col.Iterator: '__next__',  # cannot check iterator without destroying it
}


# must be cleaned after every use of __recursive_check_match

def __recursive_check_match(obj, type_var, type_var_dict=None) -> bool:
    if type_var_dict is None:
        type_var_dict = {}
    if type_var in {Ellipsis, typing.Any}:
        # everything matches ellipsis (...) and Any
        return True
    if type(type_var) != _GenericAlias:
        if isinstance(type_var, typing.TypeVar):
            type_var_dict.setdefault(type_var, type(obj))
            return __recursive_check_match(obj, type_var_dict[type_var], type_var_dict)
        if hasattr(type_var, '__supertype__'):
            return __recursive_check_match(obj, type_var.__supertype__, type_var_dict)
        try:
            return isinstance(obj, type_var)
        except TypeError:
            return False
    base_class = type_var.__origin__
    args = type_var.__args__
    if base_class is list:
        if isinstance(obj, list):
            if type(obj) is not list:
                # something that inherits from list passed, we cannot be sure that iterating through it will
                # not cause damage to the program
                return True
            for val in obj:
                if not __recursive_check_match(val, args[0], type_var_dict):
                    return False
            return True
        return False
    if base_class is tuple:
        if isinstance(obj, tuple):
            if type(obj) is not tuple or len(args) == 0:
                return True
            if len(args) != len(obj):
                return False
            for i, val in enumerate(obj):
                if not __recursive_check_match(val, args[i], type_var_dict):
                    return False
            return True
        return False
    if base_class is dict:
        if isinstance(obj, dict):
            if type(obj) is not dict:
                return True
            for key, val in obj.items():
                if not __recursive_check_match(key, args[0], type_var_dict):
                    return False
                if not __recursive_check_match(val, args[1], type_var_dict):
                    return False
            return True
        return False
    if base_class is typing.Union:
        for i in args:
            if __recursive_check_match(obj, i, type_var_dict):
                return True
        return False
    if hasattr(typing, 'Literal') and base_class is typing.Literal:
        # Literal may not have been added to the typing module
        for i in args:
            if i == obj:
                # may cause problems if obj.__eq__ or has been overridden to cause damage
                return True
        return False
    if base_class is type:
        if not isinstance(obj, type):
            return False
        try:
            return issubclass(obj, args[0])
        except TypeError:
            return False
    if base_class is abc_col.Iterable:
        if type(obj) in {list, tuple, dict, set}:
            # known iterables that can be iterated through without causing damage
            for val in obj:
                if not __recursive_check_match(val, args[0], type_var_dict):
                    return False
            return True
        # cannot check iterable type without causing damage
        return hasattr(obj, '__iter__')
    if base_class is set:
        if isinstance(obj, set):
            if type(obj) is not set:
                return True
            for val in obj:
                if not __recursive_check_match(val, args[0], type_var_dict):
                    return False
            return True
        return False
    if base_class is abc_col.Callable:
        if len(args) == 0:
            return hasattr(obj, '__call__')
        if obj.__annotations__.get('return') is not None and obj.__annotations__['return'] != args[1]:
            return False
        if args[0] is Ellipsis:
            return True
        specs = inspect.getfullargspec(obj)
        if len(specs.args) != len(args[0]):
            return False
        for idx, i in enumerate(specs.args):
            if obj.__annotations__.get(i) is not None and obj.__annotations__[i] != args[0][idx]:
                return False
        return True
    if base_class is abc_col.Mapping:
        if type(obj) is dict:
            # only known safe mapping type
            for key, val in obj.items():
                if not __recursive_check_match(key, args[0], type_var_dict):
                    return False
                if not __recursive_check_match(val, args[1], type_var_dict):
                    return False
            return True
        # cannot check mapping type without causing damage
        return hasattr(obj, '__getitem__')
    if base_class is abc_col.Sequence:
        if type(obj) in {list, tuple, dict}:
            # known sequences that can be iterated through without causing damage
            for val in obj:
                if not __recursive_check_match(val, args[0], type_var_dict):
                    return False
            return True
        # cannot check iterable type without causing damage
        return hasattr(obj, '__getitem__') and hasattr(obj, '__len__')
    if base_class in __SINGLE_ATTR_DICT:
        return hasattr(obj, __SINGLE_ATTR_DICT[base_class])
    print(f'type {base_class} has no implemented way of checking it, to resolve'
          f' this you may submit an issue in https://github.com/idoheinemann/python-overload/issues')


def __get_best_match(lst, name, *args, **kwargs):
    nominated = []
    for func in lst:
        specs = inspect.getfullargspec(func)
        defaults = specs.defaults
        defaults = 0 if defaults is None else len(defaults)
        to_continue = False
        if len(specs.args) - defaults > len(args) + len(kwargs):  # not enough arguments
            continue
        if specs.varkw is None:  # check for non existing argument
            for i in kwargs:
                if i not in specs.args and i not in specs.kwonlyargs:
                    to_continue = True
                    break
            if to_continue:
                continue
        if specs.varargs is None:
            if len(args) > len(specs.args):  # too many arguments
                continue
        if specs.varargs is None or len(args) <= len(specs.args):
            filled_args = specs.args[len(args):]
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
        if specs.varkw is None and specs.varargs is None:
            default_vars = specs.args[len(specs.args) - defaults:]
            filled_twice = 0
            for i in kwargs:
                if i in default_vars:
                    filled_twice += 1
            if len(args) > len(specs.args) - defaults:
                filled_twice += len(args) - len(specs.args) + defaults
            if len(specs.args) != len(args) + len(kwargs) - filled_twice:  # amount of arguments not ok
                continue

        nominated.append(func)
    if len(nominated) == 0:
        raise AttributeError(f"no implementation of '{name}' matches given arguments")
    if len(nominated) > 1:
        best_score = -1
        best_amount = 0
        best_func = None
        for f in nominated:
            score = 0
            specs = inspect.getfullargspec(f)
            for i, n in enumerate(specs.args):
                ann = f.__annotations__.get(n)
                if ann is None:
                    continue
                if len(args) > i:  # variable in args
                    if __recursive_check_match(args[i], ann):
                        score += 1
                elif n in kwargs:
                    if __recursive_check_match(kwargs[n], ann):
                        score += 1
            if f.__annotations__.get(specs.varargs) is not None:
                if __recursive_check_match(args[len(specs.args):], f.__annotations__[specs.varargs]):
                    score += 1
            if f.__annotations__.get(specs.varkw) is not None:
                kwcopy = {}
                for i in kwargs:
                    if i not in specs.args and i not in specs.kwonlyargs:
                        kwcopy[i] = kwargs[i]
                if __recursive_check_match(kwcopy, f.__annotations__[specs.varkw]):
                    score += 1
            for n in specs.kwonlyargs:
                ann = f.__annotations__.get(n)
                if ann is None:
                    continue
                elif n in kwargs:
                    if __recursive_check_match(kwargs[n], ann):
                        score += 1
            if score == best_score:
                best_amount += 1
            elif score > best_score:
                best_amount = 1
                best_score = score
                best_func = f
        if best_amount > 1 or best_func is None:
            raise AttributeError(f"too many possible implementations of {name} match the given arguments")
        return best_func
    return nominated[0]


def overload(func):
    name = __func_name(func)
    __overloaded_functions.setdefault(name, set())
    __overloaded_functions[name].add(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        if name in __override_queue:
            __override_resolve(name)
        return __get_best_match(__overloaded_functions[name], name, *args, **kwargs)(*args, **kwargs)

    return wrapper


def __override_resolve(name):
    # doing it lazy because when done not lazy, class does not exist because it hasn't finished loading yet
    __override_queue.remove(name)
    func = __overloaded_functions[name]
    if len(func) == 0:
        return
    first_func = next(iter(func))
    # some things are the same for all funcs, so we will use the first
    base_class: typing.Optional[type] = __get_class_that_defined_method(first_func)
    # cannot find base class, continue as usual
    if base_class is None:
        return
    override_not_found = True
    for cls in base_class.mro()[1:]:  # skipping this class, as it is first in the mro
        if first_func.__name__ in cls.__dict__:  # all funcs have the same name
            override_not_found = False
            derived_name = __func_name(cls.__dict__[first_func.__name__])
            if derived_name in __override_queue:
                __override_resolve(derived_name)

            if derived_name in __overloaded_functions:
                for f in __overloaded_functions[derived_name]:
                    for f2 in func:
                        if __compare_specs(f, f2):
                            break
                    else:
                        __overloaded_functions[name].add(f)

    if override_not_found:
        raise SyntaxError(f'function {name} is not overriden, yet declared as such')


def override(func):
    name = __func_name(func)
    if __get_meth_class_name(func) == '':
        raise SyntaxError(f'function {name} is not a method and cannot be overriden')

    __override_queue.add(name)
    # must overload to put this function in the overloaded set

    return overload(func)


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


    @overload
    def t(v: int):
        return f'int{v}'


    @overload
    def t(v: float):
        return f'float{v}'


    @overload
    def t(v: typing.List[typing.Union[int, float]]):
        return f'list{v}'


    print(t(7))
    print(t(5.2))
    print(t([1, 2, 5.5]))

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
