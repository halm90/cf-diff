"""
Unit tests for the cf-diff tool parameters module
"""
import os
import pytest
import unittest

from mock import patch, MagicMock

import parameters

#pylint: disable=protected-access, invalid-name

class TestParams(unittest.TestCase):
    """
    Test basic operation of the class.
    """
    def testParamOK(self):
        """
        Test the Sysparams object 'happy' path
        """
        test_env = {'OAUTH_CLIENT_ID': 'id',
                    'OAUTH_CLIENT_SECRET': 'shhh',
                    'FOUNDATION': 'foundation',
                    'CC_URL': 'e/f/g/h'}
        with patch.dict(os.environ, test_env) as mock_env:
            param = parameters.SysParams()
        self.assertEqual(param, test_env)

    def testParamMissing(self):
        """
        Test the Sysparams object 'sad' path
        """
        make_missing = 'FOUNDATION'
        test_env = {'OAUTH_CLIENT_ID': 'id',
                    'OAUTH_CLIENT_SECRET': 'shhh',
                    'CC_URL': 'e/f/g/h'}
        with patch.dict(os.environ, test_env) as mock_env, \
             pytest.raises(parameters.MissingEnvironmentVariable):
            try:
                os.environ.pop(make_missing)
            except KeyError:
                pass
            param = parameters.SysParams().reload()
