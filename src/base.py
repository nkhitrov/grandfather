import inspect
from functools import wraps
import types

trace_types = (
    types.MethodType,
    types.FunctionType,
    types.BuiltinFunctionType,
    types.BuiltinMethodType,
    types.MethodDescriptorType,
    types.ClassMethodDescriptorType,
)

_inspector_registry = {}


def context(*, pre_hook=None, post_hook=None, subcontexts=None):
    def _decorator(klass):
        _apply_default_hook_policy(klass=klass, pre_hook=pre_hook, post_hook=post_hook)
        _register_class_inspector(klass=klass)
        _subcontexts = set(subcontexts) if subcontexts else set()

        _apply_default_inspector_policy(klass=klass, subcontexts=_subcontexts)
        return klass

    return _decorator


def _apply_default_inspector_policy(*, klass, subcontexts):
    klass_inspector = _inspector_registry.get(klass)["inspector"]

    fields = inspect.get_annotations(klass).values()
    init_params = inspect.get_annotations(klass.__init__).values()
    all_params = set(fields) | set(set(init_params))

    for field in all_params:
        inspector = _inspector_registry.get(field)["inspector"]
        if klass_inspector != inspector and inspector not in subcontexts:
            raise TypeError(
                f"Class '{field.__name__}' can not be used in context '{klass_inspector.__name__}' because it used in context '{inspector.__name__}'"
            )


def meta_context(*, pre_hook=None, post_hook=None, subcontexts=None):
    class ContextMeta(type):
        def __new__(cls, name, bases, class_dict):
            klass = super().__new__(cls, name, bases, class_dict)
            return context(
                pre_hook=pre_hook, post_hook=post_hook, subcontexts=subcontexts
            )(klass)

    return ContextMeta


def _apply_default_hook_policy(*, klass, pre_hook, post_hook):
    functions = [f for f in dir(klass) if _default_hook_function_filter(f)]

    for key in functions:
        func = getattr(klass, key)
        if isinstance(func, trace_types):
            wrapped = _set_hooks(func=func, pre_hook=pre_hook, post_hook=post_hook)
            setattr(klass, key, wrapped)


def _default_hook_function_filter(func):
    return not (func.startswith("__" or func.endswith("__")))


def _register_class_inspector(*, klass: type):
    print(klass)
    if klass.__base__ == object:
        _inspector_registry[klass] = {"inspector": klass}
        return

    for parent in klass.__mro__:
        if parent in [klass, object]:
            continue
        print("parent", parent)

        inspector = _inspector_registry[parent]["inspector"]

        _inspector_registry[klass] = {"inspector": inspector}


def _set_hooks(*, func, pre_hook, post_hook):
    if hasattr(func, "__hooks_configured"):  # Only decorate once
        return func

    @wraps(func)
    def wrapper(klass=None, *args, **kwargs):
        if pre_hook:
            pre_hook(*args, **kwargs)

        # static method hasn't cls or self argument
        if klass:
            result = func(klass, *args, **kwargs)
        else:
            result = func(*args, **kwargs)

        if post_hook:
            post_hook(result)
        return result

    wrapper.__hook_configured = True
    return wrapper
