"""
A general purpose singleton metaclass.
"""

class Singleton(type):
    """
    Basic singleton type
    """
    def __call__(cls, *args, **kwargs):
        """
        Override the type 'call'
        """
        try:
            if not cls.__instance:
                raise AttributeError
            else:
                return cls.__instance
        except AttributeError:
            cls.__instance = super().__call__(*args, **kwargs)
            return cls.__instance
