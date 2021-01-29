"""
application-wide parameters
"""
import os

from singleton import Singleton

class MissingEnvironmentVariable(Exception):
    """
    Required environment variable is missing
    """

class SysParams(dict, metaclass=Singleton):
    """
    A utility class intended to hold all system-wide and configurable
    parameters.
    """
    _required_env = ['OAUTH_CLIENT_ID', 'OAUTH_CLIENT_SECRET',
                     'FOUNDATION', 'CC_URL']

    _overridable = {
    }

    def __init__(self):
        super().__init__()
        self.reload()

    def reload(self):
        #  Get required environment variables, fail if any are missing.
        missing = []
        for key in self._required_env:
            try:
                self[key] = os.environ[key]
            except KeyError:
                missing.append(key)
        if missing:
            raise MissingEnvironmentVariable("Missing {}".format(', '.join(missing)))

        #  Get optional/overridable environment variables
        self.update({key: os.getenv(key, val) for
                     key, val in self._overridable.items()})
