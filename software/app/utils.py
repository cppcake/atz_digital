# This singelton implementation is sourced from the python documentation: https://www.python.org/download/releases/2.2/descrintro/#__new__


class Singleton(object):
    """Singleton base class. Provides lazy, onetime initialization through the init_lazy method."""

    def __new__(cls, *args, **kwargs):
        # Look for existing instance and return existing.
        instance = cls.__dict__.get("__it__")
        if instance is not None:
            return instance

        # If no instance exists yet create a new instance and call init_lazy on it.
        cls.__it__ = instance = object.__new__(cls)
        instance.init_lazy(*args, **kwargs),
        return instance

    def init_lazy(self, *args, **kwargs):
        """Lazy, onetime initialization should happen here. Implementors should implement this instead if __init__"""
        ...
